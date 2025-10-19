# Sprint WMS Phase 2 - Implementation Plan
## Receiving + UoM/Case-Pack + RBAC UI + Catalog Sync Hardening

**Start Date:** October 19, 2025  
**Target Completion:** 10-12 days  
**Design Reference:** Manhattan Associates Active WMS  
**Language:** Serbian (Srpski)  
**Feature Flags:** FF_RECEIVING, FF_UOM_PACK, FF_RBAC_UI

---

## 🎯 Executive Summary

Build on Phase 1's Manhattan-style foundation to deliver:
- ✅ **Receiving (Prijem)** - Full E2E inbound workflow with photo attachments
- ✅ **UoM/Case-Pack** - BOX↔PCS conversion throughout system
- ✅ **Catalog Sync Hardening** - Incremental, throttled, monitored
- ✅ **RBAC UI** - User/role administration with visibility policies
- ✅ **Telemetry** - Performance monitoring & alerts

**Build Upon:**
- Phase 1 Manhattan components (Header, Home, Navigation)
- Phase 1 Serbian i18n (sr-comprehensive.ts)
- Phase 1 Zebra optimizations (48px tap targets)

---

## 📋 Implementation Roadmap (180 Points)

### Phase 2.1: Backend Foundation (Days 1-3)

#### 1.1 Receiving Entities & Migration

**Database Schema:**
```sql
CREATE TABLE receiving_header (
    id UUID PRIMARY KEY,
    broj_prijema VARCHAR(64) UNIQUE NOT NULL,
    dobavljac_id UUID REFERENCES subjects(id),
    magacin_id UUID REFERENCES magacin(id),
    datum DATE NOT NULL,
    status receiving_status_enum DEFAULT 'novo',
    created_by_id UUID REFERENCES users(id),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    completed_by_id UUID REFERENCES users(id),
    meta JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE receiving_item (
    id UUID PRIMARY KEY,
    header_id UUID REFERENCES receiving_header(id) ON DELETE CASCADE,
    artikal_id UUID REFERENCES artikal(id),
    sifra VARCHAR(64) NOT NULL,
    naziv VARCHAR(255) NOT NULL,
    jedinica_mjere VARCHAR(32) NOT NULL,
    kolicina_trazena NUMERIC(12,3) NOT NULL,
    kolicina_primljena NUMERIC(12,3) DEFAULT 0,
    razlog receiving_reason_enum,
    napomena TEXT,
    attachments JSONB DEFAULT '[]',
    status receiving_item_status_enum DEFAULT 'novo',
    completed_at TIMESTAMP,
    completed_by_id UUID REFERENCES users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TYPE receiving_status_enum AS ENUM (
    'novo',                    -- New
    'u_toku',                  -- In progress
    'završeno',                -- Completed full
    'završeno_djelimično'      -- Completed partial
);

CREATE TYPE receiving_reason_enum AS ENUM (
    'manjak',                  -- Shortage
    'višak',                   -- Overage
    'oštećeno',                -- Damaged
    'nije_isporučeno',         -- Not delivered
    'drugo'                    -- Other (custom)
);

CREATE TYPE receiving_item_status_enum AS ENUM (
    'novo',
    'u_toku',
    'gotovo'
);

-- Indexes
CREATE INDEX idx_receiving_header_broj ON receiving_header(broj_prijema);
CREATE INDEX idx_receiving_header_status ON receiving_header(status);
CREATE INDEX idx_receiving_header_datum ON receiving_header(datum);
CREATE INDEX idx_receiving_header_magacin ON receiving_header(magacin_id);
CREATE INDEX idx_receiving_item_header ON receiving_item(header_id);
CREATE INDEX idx_receiving_item_artikal ON receiving_item(artikal_id);
```

**Migration File:** `20251019_add_receiving_entities.py`

---

#### 1.2 UoM / Case-Pack Extension

**Extend Artikal Model:**
```sql
ALTER TABLE artikal
ADD COLUMN base_uom VARCHAR(32) DEFAULT 'PCS',
ADD COLUMN pack_uom VARCHAR(32),
ADD COLUMN conversion_factor NUMERIC(8,3),
ADD COLUMN is_primary_pack BOOLEAN DEFAULT false,
ADD CONSTRAINT ck_conversion_factor_positive 
    CHECK (conversion_factor IS NULL OR conversion_factor > 0);

-- Example data:
-- artikal: "Coca Cola"
-- base_uom: 'PCS' (piece)
-- pack_uom: 'BOX' (box)
-- conversion_factor: 12 (12 PCS per BOX)

CREATE INDEX idx_artikal_pack_uom ON artikal(pack_uom);
```

**Conversion Rules:**
```python
# Always store in base_uom (PCS)
def convert_to_base(quantity: float, uom: str, article: Artikal) -> float:
    if uom == article.base_uom:
        return quantity
    elif uom == article.pack_uom and article.conversion_factor:
        return quantity * float(article.conversion_factor)
    else:
        raise ValueError(f"Unknown UoM: {uom}")

# Display can show BOX equivalent
def convert_to_pack(quantity: float, article: Artikal) -> float:
    if article.conversion_factor:
        return quantity / float(article.conversion_factor)
    return quantity
```

---

#### 1.3 Catalog Sync Hardening

**Sync Strategy:**
```python
# Nightly full sync
@scheduler.scheduled_job('cron', hour=3, minute=0)
async def full_catalog_sync():
    await sync_catalog(mode='full')

# Hourly delta sync
@scheduler.scheduled_job('cron', minute=0)
async def delta_catalog_sync():
    last_sync = await get_last_sync_timestamp()
    await sync_catalog(mode='delta', since=last_sync)

# Throttling
class CatalogSyncService:
    rate_limiter = RateLimiter(max_rps=5)
    
    async def sync_catalog(self, mode='delta', since=None):
        # Use ThrottledPantheonClient from Phase 1
        client = ThrottledPantheonClient(...)
        
        # Incremental sync
        articles = await client.get_articles(time_chg_ts=since)
        
        # Upsert with conflict resolution
        for article in articles:
            await upsert_article(article)
        
        # Update sync status
        await update_sync_status('catalog', success=True, count=len(articles))
```

**Metrics:**
```python
# Prometheus metrics
catalog_sync_duration = Histogram('catalog_sync_duration_seconds')
catalog_upserts_total = Counter('catalog_upserts_total')
catalog_skipped_total = Counter('catalog_skipped_total')
catalog_errors_total = Counter('catalog_errors_total')
catalog_sync_status = Gauge('catalog_sync_status')  # 1=OK, 0=Degraded
```

---

### Phase 2.2: Backend API Implementation (Days 4-5)

#### 2.1 Receiving Endpoints

```python
# File: backend/services/task_service/app/routers/receiving.py

@router.get("/receiving")
async def list_receiving(
    status: Optional[ReceivingStatus] = None,
    datum_od: Optional[date] = None,
    datum_do: Optional[date] = None,
    magacin_id: Optional[UUID] = None,
    dobavljac_id: Optional[UUID] = None,
    broj_prijema: Optional[str] = None,
) -> List[ReceivingHeaderResponse]:
    """List receiving documents with filters"""
    pass

@router.get("/receiving/{id}")
async def get_receiving(id: UUID) -> ReceivingDetailResponse:
    """Get receiving header + items"""
    pass

@router.post("/receiving/import")
async def import_receiving(file: UploadFile) -> ImportResponse:
    """Import receiving from CSV/XLSX (idempotent)"""
    pass

@router.post("/receiving/{id}/start")
async def start_receiving(id: UUID) -> ReceivingHeaderResponse:
    """Set status to 'u_toku'"""
    pass

@router.post("/receiving/items/{item_id}/receive")
async def receive_item(
    item_id: UUID,
    request: ReceiveItemRequest  # {quantity, reason?, note?, photoIds?}
) -> ReceiveItemResponse:
    """Record received quantity for item"""
    pass

@router.post("/receiving/{id}/complete")
async def complete_receiving(id: UUID) -> CompleteReceivingResponse:
    """Complete receiving (full or partial)"""
    pass

@router.get("/receiving/{id}/report")
async def get_receiving_report(
    id: UUID,
    format: Literal['pdf', 'csv'] = 'pdf'
) -> FileResponse:
    """Generate report with photos"""
    pass
```

#### 2.2 Photo Upload Service

```python
# File: backend/services/task_service/app/services/photo_upload.py

class PhotoUploadService:
    """Handle photo attachments from PWA camera"""
    
    async def upload_photo(
        self,
        base64_data: str,
        filename: str,
        receiving_item_id: UUID
    ) -> str:
        """
        Upload photo to storage
        Returns: photo_id (S3 key or file path)
        """
        # Decode base64
        image_data = base64.b64decode(base64_data)
        
        # Generate unique filename
        photo_id = f"receiving/{receiving_item_id}/{uuid.uuid4()}.jpg"
        
        # Save to storage (filesystem or S3)
        await save_to_storage(photo_id, image_data)
        
        # Create thumbnail
        thumbnail_id = await create_thumbnail(photo_id)
        
        return photo_id
    
    async def get_photo_url(self, photo_id: str) -> str:
        """Get public URL for photo"""
        return f"/api/photos/{photo_id}"
```

---

### Phase 2.3: PWA Receiving Components (Days 6-7)

#### 3.1 Receiving List Page

**File:** `frontend/pwa/src/pages/ReceivingListPage.tsx`

```tsx
/**
 * Receiving List Page (Serbian: Prijemi)
 * Manhattan Active WMS style
 */

Layout:
┌─────────────────────────────────┐
│ ManhattanHeader                 │
├─────────────────────────────────┤
│ Prijemi                         │
│ [Filter: Svi ▼] [🔍 Pretraži]  │
│                                 │
│ ┌─────────────────────────────┐│
│ │ RECV-001                    ││
│ │ Dobavljač: ABC d.o.o.       ││
│ │ Datum: 19.10.2025           ││
│ │ Status: U toku 🟡          ││
│ │ Stavke: 5/10 primljeno      ││
│ └─────────────────────────────┘│
│                                 │
│ ┌─────────────────────────────┐│
│ │ RECV-002                    ││
│ │ Dobavljač: XYZ d.o.o.       ││
│ │ Datum: 18.10.2025           ││
│ │ Status: Završeno ✅        ││
│ │ Stavke: 15/15 primljeno     ││
│ └─────────────────────────────┘│
└─────────────────────────────────┘

Features:
- Card-based list (Manhattan pattern)
- Filter by status
- Search by broj_prijema
- Status badges with colors
- Progress indicators
- Pull-to-refresh
```

#### 3.2 Receiving Detail Page

**File:** `frontend/pwa/src/pages/ReceivingDetailPage.tsx`

```tsx
Layout:
┌──────────────────────────────────┐
│ ← RECV-001                       │
│ Dobavljač: ABC d.o.o.            │
│ Datum: 19.10.2025                │
│                                  │
│ [Sve] [Ostalo] [Djelimično]     │← Quick filters
│                                  │
│ ┌──────────────────────────────┐│
│ │ 12345 - Test Artikal         ││
│ │ Traženo: 100 PCS             ││
│ │ Primljeno: 88 PCS            ││
│ │ [-] [88] PCS [+]             ││← Large stepper
│ │                              ││
│ │ Razlog: ▼ [Manjak      ]    ││
│ │ Napomena: [____________]     ││
│ │ 📷 Dodaj fotografiju         ││
│ │ [Sačuvaj stavku]             ││
│ └──────────────────────────────┘│
│                                  │
│ [Završi prijem]                  │← Bottom button
└──────────────────────────────────┘

Features:
- Master/detail list
- Item-by-item receiving
- Quantity stepper (reuse from Phase 1)
- Reason dropdown
- Note field
- Camera photo button
- Photo preview thumbnails
- Quick filters
- Complete button (always enabled)
```

#### 3.3 Camera Component

**File:** `frontend/pwa/src/components/CameraCapture.tsx`

```tsx
import React, { useRef, useState } from 'react';
import { Button, Modal, Space } from 'antd';
import { CameraOutlined, DeleteOutlined, CheckOutlined } from '@ant-design/icons';

export const CameraCapture: React.FC = ({ onCapture }) => {
  const videoRef = useRef<HTMLVideoElement>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [capturedPhoto, setCapturedPhoto] = useState<string | null>(null);

  const openCamera = async () => {
    const mediaStream = await navigator.mediaDevices.getUserMedia({
      video: { facingMode: 'environment', width: 1280, height: 720 }
    });
    setStream(mediaStream);
    if (videoRef.current) {
      videoRef.current.srcObject = mediaStream;
    }
  };

  const capturePhoto = () => {
    const canvas = document.createElement('canvas');
    canvas.width = 1280;
    canvas.height = 720;
    const context = canvas.getContext('2d');
    context?.drawImage(videoRef.current!, 0, 0);
    const dataUrl = canvas.toDataURL('image/jpeg', 0.8);
    setCapturedPhoto(dataUrl);
  };

  const confirmPhoto = () => {
    onCapture(capturedPhoto);
    closeCamera();
  };

  return (
    <Modal open={!!stream} onCancel={closeCamera}>
      {/* Camera UI */}
    </Modal>
  );
};
```

---

### Phase 2.4: Admin Receiving UI (Days 8-9)

#### 4.1 Receiving List Table

**File:** `frontend/admin/src/pages/ReceivingPage.tsx`

```tsx
Columns:
┌────────┬───────────┬──────────┬──────┬────────┬─────────┬────────┐
│ Broj   │ Dobavljač │ Magacin  │ Datum│ Status │ % prijem│ Akcije │
├────────┼───────────┼──────────┼──────┼────────┼─────────┼────────┤
│RECV-001│ABC d.o.o. │Magacin 1 │19.10 │U toku🟡│  88%    │ 👁️📊  │
│RECV-002│XYZ d.o.o. │Magacin 1 │18.10 │Završ.✅│ 100%    │ 👁️📊  │
└────────┴───────────┴──────────┴──────┴────────┴─────────┴────────┘

Features:
- Sticky header
- Server-side filters
- Sort by any column
- Status badges (color-coded)
- % prijem progress bar
- Actions: View, Report
- CSV export
```

#### 4.2 Receiving Import Modal

```tsx
<Modal title="Import prijema (CSV/XLSX)">
  <Dragger
    accept=".csv,.xlsx"
    maxCount={1}
    maxSize={10 * 1024 * 1024}  // 10MB
  >
    Prevucite fajl ili kliknite za upload
  </Dragger>
  
  {/* Preview table after upload */}
  {preview && (
    <Table 
      dataSource={preview.rows} 
      pagination={false}
      scroll={{ y: 300 }}
    />
  )}
  
  <Alert type="info">
    Duplikati (broj_prijema) biće preskočeni
  </Alert>
  
  <Button type="primary" loading={importing}>
    Uvezi ({preview.rows.length} redova)
  </Button>
</Modal>
```

#### 4.3 Receiving Detail View

```tsx
Master/Detail:
┌─────────────────────────────────────────────────┐
│ RECV-001 - ABC d.o.o. - 19.10.2025              │
│ Status: U toku 🟡 | % prijem: 88%               │
├─────────────────────────────────────────────────┤
│ Stavke (10):                                    │
│ ┌─────────────────────────────────────────────┐│
│ │Šifra  │Naziv       │Traženo│Primljeno│%│Razlog││
│ ├───────┼────────────┼───────┼─────────┼─┼─────┤│
│ │12345  │Test Artikal│100 PCS│88 PCS   │88│Manjak││
│ │       │📷📷        │       │         │ │     ││← Photo thumbnails
│ └─────────────────────────────────────────────┘│
└─────────────────────────────────────────────────┘

Features:
- Expandable rows (show napomena, photos)
- Photo gallery modal
- Reason chips
- % completion per item
- Export to PDF/CSV with photos
```

---

### Phase 2.5: Users & Roles UI (Days 10-11)

#### 5.1 Users Management Page

**File:** `frontend/admin/src/pages/UsersRolesPage.tsx`

```tsx
Table:
┌────────┬─────────────┬────────┬──────┬────────┬────────┐
│ Ime    │ Email       │ Uloga  │ Tim  │ Aktivan│ Akcije │
├────────┼─────────────┼────────┼──────┼────────┼────────┤
│Sabin M.│sabin@...    │Magacion│Tim A1│   ✅   │ ✏️🔑🗑️ │
│Gezim M.│gezim@...    │Magacion│Tim A1│   ✅   │ ✏️🔑🗑️ │
│Admin   │admin@...    │Admin   │  -   │   ✅   │ ✏️🔑   │
└────────┴─────────────┴────────┴──────┴────────┴────────┘

Actions:
✏️ Edit (role, team assignment)
🔑 Reset password
🗑️ Deactivate
```

#### 5.2 Create/Edit User Modal

```tsx
<Form layout="vertical">
  <Form.Item label="Ime" required>
    <Input placeholder="Unesite ime" />
  </Form.Item>
  
  <Form.Item label="Email" required>
    <Input type="email" />
  </Form.Item>
  
  <Form.Item label="Uloga" required>
    <Select>
      <Option value="admin">Administrator</Option>
      <Option value="menadzer">Menadžer</Option>
      <Option value="sef">Šef</Option>
      <Option value="komercijalista">Komercijalista</Option>
      <Option value="magacioner">Magacioner</Option>
    </Select>
  </Form.Item>
  
  {role === 'magacioner' && (
    <Form.Item label="Tim">
      <Select>
        <Option value="team-a1">Tim A1 (Smjena A)</Option>
        <Option value="team-b1">Tim B1 (Smjena B)</Option>
      </Select>
    </Form.Item>
  )}
  
  <Form.Item label="Početna lozinka">
    <Input.Password />
  </Form.Item>
</Form>
```

#### 5.3 RBAC Visibility Middleware

```python
# File: backend/services/task_service/app/middleware/rbac.py

async def filter_tasks_by_role(user: UserAccount, tasks: List[Zaduznica]) -> List[Zaduznica]:
    """
    Apply RBAC visibility policy
    
    magacioner: Only my tasks + team tasks
    sef: All tasks in my magacin
    menadzer: All tasks globally
    admin: All tasks globally
    """
    if user.role == Role.MAGACIONER:
        # Filter: assigned to me OR assigned to my team
        my_team_id = await get_user_team_id(user.id)
        return [
            t for t in tasks 
            if t.magacioner_id == user.id or t.team_id == my_team_id
        ]
    
    elif user.role == Role.SEF:
        # Filter: tasks in same magacin as user
        user_magacin = await get_user_magacin(user.id)
        return [
            t for t in tasks
            if t.trebovanje.magacin_id == user_magacin
        ]
    
    else:
        # menadzer, admin: see all
        return tasks
```

---

### Phase 2.6: Feature Flags (Day 1)

```python
# File: backend/app_common/feature_flags.py

from enum import Enum

class FeatureFlag(str, Enum):
    FF_RECEIVING = "FF_RECEIVING"
    FF_UOM_PACK = "FF_UOM_PACK"
    FF_RBAC_UI = "FF_RBAC_UI"

class FeatureFlagService:
    _flags = {
        FeatureFlag.FF_RECEIVING: True,
        FeatureFlag.FF_UOM_PACK: True,
        FeatureFlag.FF_RBAC_UI: True,
    }
    
    @classmethod
    def is_enabled(cls, flag: FeatureFlag) -> bool:
        return cls._flags.get(flag, False)
    
    @classmethod
    def set_flag(cls, flag: FeatureFlag, enabled: bool):
        cls._flags[flag] = enabled

# Usage in routers
from app_common.feature_flags import FeatureFlagService, FeatureFlag

@router.get("/receiving")
async def list_receiving(...):
    if not FeatureFlagService.is_enabled(FeatureFlag.FF_RECEIVING):
        raise HTTPException(404, "Feature not enabled")
    # ... implementation
```

---

## 📝 Serbian Language Extensions

```typescript
// File: frontend/pwa/src/i18n/sr-phase2.ts

export const srPhase2 = {
  receiving: {
    prijem: "Prijem",
    prijemi: "Prijemi",
    brojPrijema: "Broj prijema",
    dobavljac: "Dobavljač",
    primljeno: "Primljeno",
    
    // Status
    novo: "Novo",
    uToku: "U toku",
    zavrseno: "Završeno",
    zavrsenoDjelimicno: "Završeno (djelimično)",
    
    // Reasons
    manjak: "Manjak",
    visak: "Višak",
    osteceno: "Oštećeno",
    nijeIsporuceno: "Nije isporučeno",
    
    // Actions
    zapocniPrijem: "Započni prijem",
    zavrsiPrijem: "Završi prijem",
    primiteStavku: "Primite stavku",
    dodajFotografiju: "Dodaj fotografiju",
    slikajFotografiju: "Slikaj fotografiju",
    
    // Messages
    stavkaAzurirana: "Stavka ažurirana",
    prijemZavrsen: "Prijem završen",
    prijemZavrsenDjelimicno: "Prijem završen (djelimično)",
  },
  
  uom: {
    jedinicaMjere: "Jedinica mjere",
    osnovna: "Osnovna",
    pakovanje: "Pakovanje",
    faktorKonverzije: "Faktor konverzije",
    komada: "komada",
    kutija: "kutija",
    paket: "paket",
  },
  
  rbac: {
    korisnici: "Korisnici",
    uloge: "Uloge",
    dodijeliUlogu: "Dodijeli ulogu",
    dodijeliTim: "Dodijeli tim",
    resetujLozinku: "Resetuj lozinku",
    deaktiviraj: "Deaktiviraj",
    aktiviraj: "Aktiviraj",
    
    // Roles
    administrator: "Administrator",
    menadzer: "Menadžer",
    sef: "Šef",
    komercijalista: "Komercijalista",
    magacioner: "Magacioner",
    
    // Permissions
    potpunPristup: "Potpun pristup",
    ogranicenPristup: "Ograničen pristup",
    samoSvojiZadaci: "Samo svoji zadaci",
    zadaciTima: "Zadaci tima",
    zadaciLokacije: "Zadaci lokacije",
  }
};
```

---

## 🧪 Test Cases (20 Required)

### Test Category Breakdown:

**Receiving (8 tests):**
1. Import receiving CSV
2. Start receiving
3. Receive item (full quantity)
4. Receive item (partial with reason)
5. Add photo attachment
6. Complete receiving (full)
7. Complete receiving (partial)
8. Generate PDF report with photos

**UoM/Case-Pack (4 tests):**
9. Import with BOX quantities → convert to PCS
10. PWA shows PCS consistently
11. KPI metrics in PCS
12. CSV export in PCS

**RBAC (4 tests):**
13. Magacioner sees only own tasks
14. Magacioner sees team tasks
15. Šef sees location tasks
16. 403 when accessing unauthorized

**Catalog Sync (3 tests):**
17. Full sync succeeds
18. Delta sync with timestamp
19. Throttling works (5 req/s)

**Performance (1 test):**
20. All endpoints < target latency

---

## 📊 Implementation Estimates

| Task | Complexity | Est. Time | Files |
|------|-----------|-----------|-------|
| Receiving Backend | High | 2 days | 8 files |
| UoM Extension | Medium | 1 day | 4 files |
| Catalog Hardening | Medium | 1 day | 3 files |
| RBAC UI | Medium | 2 days | 5 files |
| PWA Receiving | High | 2 days | 6 files |
| Camera Component | Medium | 0.5 day | 2 files |
| Telemetry | Low | 0.5 day | 2 files |
| Documentation | Medium | 2 days | 4 docs |
| Testing | High | 1 day | 1 report |
| **Total** | | **12 days** | **35+ files** |

---

## 🎯 Definition of Done

### Backend DoD:
- [ ] All migrations applied
- [ ] All endpoints respond with correct data
- [ ] Feature flags working
- [ ] Audit logging captures all events
- [ ] Performance targets met (P95 < 250ms)
- [ ] No breaking changes to existing APIs

### PWA DoD:
- [ ] Receiving list + detail functional
- [ ] Camera capture works on Zebra
- [ ] Photo upload to backend
- [ ] Offline queue for receiving operations
- [ ] Serbian labels throughout
- [ ] Tap targets >= 48px
- [ ] Tested on TC21/MC3300

### Admin DoD:
- [ ] Receiving import modal works
- [ ] Receiving table shows all data
- [ ] Photo thumbnails clickable
- [ ] Report export (PDF/CSV)
- [ ] Users & roles CRUD
- [ ] RBAC visibility working

### Documentation DoD:
- [ ] 4 new docs created
- [ ] 20 test cases documented
- [ ] Screenshots (30 total)
- [ ] README updated

---

**Status:** 🟢 Ready to Implement  
**Start:** October 19, 2025  
**Estimated Completion:** October 31, 2025


