# Receiving (Prijem Robe) - Documentation

**Feature:** Sprint WMS Phase 2  
**Pattern:** Manhattan Active WMS Inbound Workflow  
**Language:** Serbian (Srpski)  
**Status:** Implementation Complete

---

## Overview

Receiving (Prijem robe) module provides complete inbound workflow for warehouse receiving operations with:
- ✅ CSV/XLSX import of expected receipts
- ✅ Item-by-item receiving with quantity validation
- ✅ Exception handling (manjak, višak, oštećeno)
- ✅ Photo attachments via PWA camera
- ✅ Partial completion support
- ✅ PDF/CSV reporting
- ✅ Real-time updates < 2s

---

## Database Schema

### receiving_header
```sql
id UUID PRIMARY KEY
broj_prijema VARCHAR(64) UNIQUE  -- Document number
dobavljac_id UUID FK subjects    -- Supplier
magacin_id UUID FK magacin       -- Warehouse
datum DATE                        -- Receipt date
status receiving_status_enum      -- novo, u_toku, završeno, završeno_djelimično
created_by_id UUID FK users
started_at TIMESTAMP
started_by_id UUID FK users
completed_at TIMESTAMP
completed_by_id UUID FK users
meta JSONB
```

### receiving_item
```sql
id UUID PRIMARY KEY
header_id UUID FK receiving_header
artikal_id UUID FK artikal
sifra VARCHAR(64)
naziv VARCHAR(255)
jedinica_mjere VARCHAR(32)
kolicina_trazena NUMERIC(12,3)  -- Expected quantity
kolicina_primljena NUMERIC(12,3) -- Received quantity
razlog receiving_reason_enum     -- manjak, višak, oštećeno, nije_isporučeno, drugo
napomena TEXT                     -- Notes
attachments JSONB                 -- Array of photo IDs
status receiving_item_status_enum
completed_at TIMESTAMP
completed_by_id UUID FK users
```

---

## API Endpoints

### List Receivings
```http
GET /api/receiving?status=u_toku&datum_od=2025-10-01
Authorization: Bearer {token}

Response:
[
  {
    "id": "uuid",
    "broj_prijema": "RECV-001",
    "dobavljac_naziv": "ABC d.o.o.",
    "magacin_naziv": "Veleprodajni Magacin",
    "datum": "2025-10-19",
    "status": "u_toku",
    "status_serbian": "U toku",
    "completion_percentage": 88.5,
    "total_items": 10,
    "items_received": 8
  }
]
```

### Get Receiving Detail
```http
GET /api/receiving/{id}
Authorization: Bearer {token}

Response:
{
  "header": {
    "id": "uuid",
    "broj_prijema": "RECV-001",
    ...
  },
  "items": [
    {
      "id": "uuid",
      "sifra": "12345",
      "naziv": "Test Artikal",
      "kolicina_trazena": 100,
      "kolicina_primljena": 88,
      "razlog": "manjak",
      "razlog_serbian": "Manjak",
      "napomena": "Oštećena kutija",
      "attachments": ["photo-id-1", "photo-id-2"],
      "completion_percentage": 88.0,
      "is_partial": true,
      "variance": -12
    }
  ]
}
```

### Import Receiving (CSV/XLSX)
```http
POST /api/receiving/import
Content-Type: multipart/form-data
Authorization: Bearer {token}

File format (CSV):
broj_prijema,dobavljac,magacin,datum,sifra,naziv,jedinica_mjere,kolicina
RECV-001,ABC d.o.o.,Veleprodajni,2025-10-19,12345,Test Artikal,PCS,100
RECV-001,ABC d.o.o.,Veleprodajni,2025-10-19,67890,Drugi Artikal,PCS,50

Response:
{
  "success": true,
  "imported_count": 1,
  "skipped_count": 0,
  "error_count": 0,
  "receiving_ids": ["uuid"]
}
```

### Start Receiving
```http
POST /api/receiving/{id}/start
Authorization: Bearer {token}

{
  "operation_id": "start-uuid-timestamp"
}

Response:
{
  "id": "uuid",
  "status": "u_toku",
  "started_at": "2025-10-19T10:00:00Z"
}
```

### Receive Item
```http
POST /api/receiving/items/{item_id}/receive
Authorization: Bearer {token}

{
  "quantity": 88,
  "razlog": "manjak",
  "napomena": "Oštećena kutija pri isporuci",
  "photo_ids": ["photo-1", "photo-2"],
  "operation_id": "receive-item-uuid-timestamp"
}

Response:
{
  "item_id": "uuid",
  "kolicina_primljena": 88,
  "kolicina_trazena": 100,
  "variance": -12,
  "razlog": "manjak",
  "completion_percentage": 88.0,
  "message": "Manjak: primljeno 88, traženo 100 - Razlog: Manjak"
}
```

### Complete Receiving
```http
POST /api/receiving/{id}/complete
Authorization: Bearer {token}

{
  "confirm_partial": true,
  "operation_id": "complete-uuid-timestamp"
}

Response:
{
  "receiving_id": "uuid",
  "broj_prijema": "RECV-001",
  "status": "završeno_djelimično",
  "total_items": 10,
  "items_full": 8,
  "items_partial": 2,
  "items_overage": 0,
  "completion_percentage": 94.5,
  "message": "Prijem završen djelimično - 94.5% primljeno",
  "completed_at": "2025-10-19T15:30:00Z"
}
```

### Generate Report
```http
GET /api/receiving/{id}/report?format=pdf
Authorization: Bearer {token}

Response: PDF file with:
- Header info (broj, dobavljač, datum)
- Item list (traženo vs. primljeno)
- Variance details
- Reasons for discrepancies
- Photo attachments
```

---

## PWA Workflow

### 1. Navigate to Receiving
```
Home → Click "Prijem" card → Receiving List
```

### 2. Select Receiving Document
```
Receiving List → Click RECV-001 card → Receiving Detail
```

### 3. Receive Items
```tsx
For each item:
1. View traženo: 100 PCS
2. Use stepper to enter primljeno: 88
3. If < traženo, select razlog dropdown: "Manjak"
4. Add napomena (optional): "Oštećena kutija"
5. Click "Dodaj fotografiju" → Camera opens
6. Take photo → Confirm → Photo added to attachments
7. Click "Sačuvaj stavku"
8. Success toast: "Stavka ažurirana"
```

### 4. Complete Receiving
```
After all items processed:
1. Click "Završi prijem" button (bottom)
2. System calculates % completion
3. If partial (< 100%), status = "Završeno (djelimično)"
4. If full (100%), status = "Završeno"
5. Success toast with summary
```

---

## Admin Workflow

### 1. Import Receiving
```
Admin → Operations → Prijem → Click "Import"
→ Drag & Drop CSV/XLSX file
→ Preview table shows
→ Click "Uvezi"
→ Success: "Uvezeno 5 prijema"
```

### 2. View Receivings
```
Table shows:
- Broj prijema
- Dobavljač
- Magacin
- Datum
- Status (badge with color)
- % prijem (progress bar)
- Actions (View, Report)

Filters:
- Status dropdown
- Date range picker
- Magacin dropdown
- Dobavljač dropdown
```

### 3. View Detail
```
Click row → Detail modal opens

Master section:
- Broj, Dobavljač, Datum, Status

Detail section (table):
- Šifra, Naziv, Traženo, Primljeno, %, Razlog
- Click photo icon → Gallery opens
- Expandable row shows napomena
```

### 4. Export Report
```
Click "Izvezi" button → Select format (PDF/CSV)
PDF includes:
- Header with logo
- Document info
- Item table with variance
- Photo thumbnails
- Serbian labels
```

---

## Photo Attachments

### PWA Camera Workflow
```javascript
// Open camera
navigator.mediaDevices.getUserMedia({ 
  video: { facingMode: 'environment' } 
})

// Capture photo
const canvas = document.createElement('canvas');
context.drawImage(video, 0, 0, 1280, 720);
const base64 = canvas.toDataURL('image/jpeg', 0.8);

// Upload to backend
await api.post('/receiving/items/{id}/upload-photo', {
  base64_data: base64,
  filename: 'photo.jpg'
});

// Backend returns photo_id
// Add to attachments array
```

### Storage
```
Photos stored at:
/uploads/receiving/{receiving_id}/{item_id}/{photo_id}.jpg

Thumbnails generated:
/uploads/receiving/{receiving_id}/{item_id}/thumb_{photo_id}.jpg

Access via:
GET /api/photos/{path}
```

---

## UoM Conversion Examples

### Example 1: Import with BOX
```csv
broj_prijema,sifra,naziv,jedinica_mjere,kolicina
RECV-001,12345,Coca Cola,BOX,24
```

**Processing:**
```python
# Article: Coca Cola
# base_uom: PCS
# pack_uom: BOX
# conversion_factor: 12

quantity_box = 24
quantity_pcs = 24 * 12 = 288

# Stored in database: 288 PCS
```

### Example 2: Display
```python
# Database: 288 PCS
# Display options:

# Simple:
format_quantity_display(288, article, show_pack=False)
→ "288 PCS"

# With pack:
format_quantity_display(288, article, show_pack=True)
→ "288 PCS (24 BOX)"
```

### Example 3: PWA Entry
```
Worker receives 23 BOX (not 24)
PWA shows: "Traženo: 288 PCS (24 BOX)"
Worker enters: 276 PCS
Variance: -12 PCS (-1 BOX)
Razlog: "Oštećeno"
```

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| Import receiving | <2s | For 100 items |
| Start receiving | <100ms | Status update |
| Receive item | <250ms | P95 target |
| Complete receiving | <500ms | Calculate stats |
| Generate PDF | <3s | With photos |

---

## Offline Support

**Offline Queue:**
```typescript
// PWA queues operations when offline
offlineQueue.add({
  type: 'receive_item',
  item_id: '...',
  payload: {
    quantity: 88,
    razlog: 'manjak',
    napomena: '...',
    photo_ids: ['...'],
    operation_id: 'receive-...'
  }
});

// Auto-sync when online
window.addEventListener('online', async () => {
  await offlineQueue.syncAll();
});
```

---

## Error Handling

**Validation Errors (400):**
- Količina < 0
- Razlog 'drugo' without napomena
- Receiving already completed
- Invalid broj_prijema format

**Not Found (404):**
- Receiving ID not found
- Item ID not found

**Forbidden (403):**
- RBAC: Magacioner accessing other location's receiving

**Server Error (500):**
- Photo upload failed
- Database constraint violation

**Serbian Error Messages:**
```json
{
  "detail": "Količina ne može biti manja od 0",
  "error_code": "VALIDATION_ERROR"
}
```

---

## Monitoring

**Prometheus Metrics:**
```python
receiving_operations_total{operation="start|receive|complete"}
receiving_duration_seconds{operation="..."}
receiving_photos_uploaded_total
receiving_partial_ratio  # % of receivings with discrepancies
receiving_reasons_total{reason="manjak|višak|..."}
```

**Grafana Dashboard:**
- Receivings per day
- Partial completion ratio
- Top reasons for discrepancies
- Average receiving time
- Photo upload success rate

---

## Best Practices

### For Workers:
1. Always take photos of damaged items
2. Provide clear napomena for "Drugo" reason
3. Complete receiving even if partial (never block)
4. Use "Manjak" for missing items, "Višak" for extras

### For Admins:
1. Review partial receivings daily
2. Export reports for supplier disputes
3. Monitor top reasons (recurring issues)
4. Import early in the day (before receiving starts)

### For System:
1. Always convert to base_uom (PCS) on import
2. Display can show pack_uom (BOX) as tooltip
3. All KPI/reports use base_uom for consistency
4. Photos compressed before upload (< 500KB each)

---

## CSV Format

**Template:**
```csv
broj_prijema,dobavljac,magacin,datum,sifra,naziv,jedinica_mjere,kolicina
RECV-001,ABC d.o.o.,Veleprodajni Magacin,2025-10-19,12345,Test Artikal,PCS,100
RECV-001,ABC d.o.o.,Veleprodajni Magacin,2025-10-19,67890,Drugi Artikal,BOX,24
```

**Rules:**
- broj_prijema: Unique per document
- dobavljac: Must match subjects.name
- magacin: Must match magacin.naziv
- datum: YYYY-MM-DD format
- kolicina: Decimal, will be converted to base_uom

---

**Document Version:** 1.0  
**Last Updated:** October 19, 2025  
**Status:** ✅ Implementation Complete


