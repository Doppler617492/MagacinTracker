# Pantheon ERP Integration - Implementation Status

## 🎯 Project Overview
Enterprise-grade integration between CunguWMS and Pantheon ERP system to enable real-time synchronization of articles, subjects, and warehouse documents.

## ✅ COMPLETED (Phases 1-3)

### Phase 1: Environment Configuration & Authentication ✅
**Files Created:**
- `backend/app_common/pantheon_config.py` - Pydantic configuration with all ENV vars
- `backend/app_common/pantheon_client.py` - Enterprise HTTP client

**Features Implemented:**
- ✅ JWT authentication with auto-refresh (5 min before expiry)
- ✅ Rate limiting (1 RPS strict enforcement)
- ✅ Circuit breaker (3 failures → 2 min pause)
- ✅ Exponential backoff retry (3 attempts)
- ✅ All 4 Pantheon API endpoints:
  - `get_ident_wms()` - Fetch articles/catalog
  - `get_subject_wms()` - Fetch partners/subjects
  - `get_issue_doc_wms()` - Fetch outbound documents
  - `get_receipt_doc_wms()` - Fetch inbound documents

**Configuration (`pantheon_config.py`):**
```python
CUNGUWMS_BASE_URL=http://109.72.96.136:3003
CUNGUWMS_USERNAME=CunguDeklaracije
CUNGUWMS_PASSWORD=0778657825
CUNGUWMS_RATE_LIMIT_RPS=1
CUNGUWMS_RETRY_MAX=3
WMS_MAGACIN_CODE=VELE_TEST
```

### Phase 2: Database Models & Migrations ✅
**Files Created:**
- Enhanced `backend/services/task_service/app/models/article.py`
- New `backend/services/task_service/app/models/subject.py`
- New `backend/services/task_service/app/models/document.py`
- Updated `backend/services/task_service/app/models/enums.py`
- Migration: `alembic/versions/2025101701_pantheon_erp_integration.py`

**Database Schema:**

1. **artikal** (Enhanced)
   - Added: `supplier`, `article_class`, `description`
   - Added: `time_chg_ts`, `last_synced_at`, `source`
   - Index on `time_chg_ts` for delta sync

2. **subjects** (New)
   - Partners/Suppliers/Warehouses
   - Fields: code, name, type (enum), pib, address, contact info
   - Sync tracking: `time_chg_ts`, `last_synced_at`

3. **doc_types** (New)
   - Document type catalog
   - Fields: code, name, direction (inbound/outbound)

4. **receipts** (New) + **receipt_items** (New)
   - Inbound documents from Pantheon
   - Item fields: code, name, unit, barcode, qty_requested, qty_completed
   - Status tracking: new/partial/done
   - Reason for missing items

5. **dispatches** (New) + **dispatch_items** (New)
   - Outbound documents from Pantheon
   - **Critical WMS fields:**
     - `exists_in_wms` - Item matched in catalog + correct warehouse
     - `wms_flag` - Item eligible for WMS task creation
     - `warehouse_code` - Source warehouse code
   - Item status + reason tracking

**New Enums:**
- `SubjectType`: SUPPLIER, CUSTOMER, WAREHOUSE
- `DocumentDirection`: INBOUND, OUTBOUND
- `DocumentItemStatus`: NEW, PARTIAL, DONE
- `SyncAction`: CATALOG_SYNC, SUBJECTS_SYNC, ISSUE_SYNC, RECEIPT_SYNC, etc.

### Phase 3: Catalog Sync Service ✅ (In Progress)
**Files Created:**
- `backend/services/catalog_service/app/sync/pantheon_catalog_sync.py`

**Features Implemented:**
- ✅ Delta sync based on `time_chg_ts`
- ✅ Pagination (1000 items/page)
- ✅ Upsert logic for articles and barcodes
- ✅ Inactive article marking (not synced for N days)
- ✅ Sync statistics tracking
- ✅ Last sync timestamp persistence

**Usage:**
```python
from sync.pantheon_catalog_sync import sync_pantheon_catalog

stats = await sync_pantheon_catalog(session, full_sync=False)
# Returns: {total_fetched, articles_created, articles_updated, barcodes_created, errors, duration}
```

## 🔄 IN PROGRESS / REMAINING (Phases 4-10)

### Phase 4: Subjects Sync Service (PENDING)
**File to Create:** `backend/services/catalog_service/app/sync/pantheon_subjects_sync.py`

**Requirements:**
- Sync partners/subjects via `GetSubjectWMS`
- Type classification: supplier, customer, warehouse
- Delta sync with `time_chg_ts`
- Mark inactive subjects

### Phase 5: Document Import Services (PENDING)
**Files to Create:**
- `backend/services/import_service/app/sync/pantheon_issue_sync.py`
- `backend/services/import_service/app/sync/pantheon_receipt_sync.py`

**Requirements:**
- **Issue (Outbound):**
  - Fetch via `GetIssueDocWMS`
  - Match items by code/barcode → `article_id`
  - Set `exists_in_wms = (article_id != null AND warehouse == WMS_MAGACIN_CODE)`
  - Only `exists_in_wms = true` creates WMS tasks
  - Deduplicate by (doc_no, doc_type_id, date)

- **Receipt (Inbound):**
  - Similar logic for inbound documents
  - Filter by warehouse for WMS tasks

- **On-Demand Lookup:**
  - If article missing → fetch via `getIdentWMS`
  - Cache result 24h
  - Audit `CATALOG_LOOKUP_API`

### Phase 6: API Gateway Routes (PENDING)
**File to Update:** `backend/services/api_gateway/app/routers/pantheon.py`

**Routes to Add:**
```
POST /api/sync/catalog          # Trigger catalog sync (ADMIN only)
POST /api/sync/subjects         # Trigger subjects sync (ADMIN only)
POST /api/sync/issue            # Trigger issue docs sync (ADMIN only)
POST /api/sync/receipt          # Trigger receipt docs sync (ADMIN only)

GET  /api/dispatches            # List outbound documents
GET  /api/dispatches/{id}       # Get document details
GET  /api/dispatches/{id}/items # Get document items
GET  /api/receipts              # List inbound documents
GET  /api/receipts/{id}         # Get document details
```

**Features:**
- JWT + RBAC (require ADMIN for sync endpoints)
- Query filters: date_from, date_to, doc_type, only_wms=true
- CSV export for WMS items

### Phase 7: Admin UI Updates (PENDING)
**Files to Update:**
- `frontend/admin/src/pages/CatalogPage.tsx` - Add ERP badge, sync button
- Create `frontend/admin/src/pages/SubjectsPage.tsx` - New page for partners
- Create `frontend/admin/src/pages/DispatchesPage.tsx` - Outbound documents
- Create `frontend/admin/src/pages/ReceiptsPage.tsx` - Inbound documents

**Features:**
- **Catalog Page:**
  - Badge: "Source: ERP (Pantheon)"
  - Last sync timestamp
  - "Sync Now" button (calls `/api/sync/catalog`)
  - Barcode count column

- **Subjects Page:**
  - List all partners
  - Filter by type (supplier, customer, warehouse)
  - Sync button

- **Documents Pages:**
  - Columns: doc_no, date, type, WMS items/total items
  - Detail view: item list with status, exists_in_wms, reason
  - Action: "Recalculate WMS flag"
  - CSV export (WMS items only)
  - Delete test/mock objects

### Phase 8: PWA Enhancements (PENDING)
**Files to Update:**
- `frontend/pwa/src/pages/TasksPage.tsx`
- `frontend/pwa/src/pages/TaskDetailPage.tsx`
- Create `frontend/pwa/src/components/ShiftDisplay.tsx`

**Features:**
- **Shift Display:**
  - Shift A (Morning): 08:00–15:00, break 10:00–10:30
  - Shift B (Afternoon): 12:00–19:00, break 14:00–14:30
  - Countdown timer for shift end and break

- **Task Interface:**
  - Progress bar per document
  - Manual quantity entry (supports decimals)
  - Reason dropdown: "Not in stock", "Damaged", "Not found"
  - "Finish Document" even if partial → status = partial

- **Team Sync:**
  - WebSocket live updates (already partially implemented)
  - Both teammates see changes instantly

### Phase 9: TV & KPI Dashboards (PENDING)
**Files to Update:**
- `frontend/tv/src/App.tsx`
- Update backend `kpi.py` to include WMS metrics

**Features:**
- Current active shift display
- Team leaderboard (by shift)
- Throughput per shift
- **WMS vs ERP ratio:** `exists_in_wms / total_items`
- Charts: daily/weekly performance by shift/team
- Partial completion ratio
- Average task duration

### Phase 10: Monitoring & Metrics (PENDING)
**Files to Create:**
- `backend/app_common/pantheon_metrics.py`

**Prometheus Metrics:**
```python
catalog_sync_duration_ms
subjects_sync_duration_ms
issue_sync_items_total
receipt_sync_items_total
sync_failures_total
pantheon_api_requests_total
pantheon_api_errors_total
pantheon_circuit_breaker_state
```

**Features:**
- Correlation ID per API call (already in client)
- Error rate tracking
- P95 latency < 300ms target
- Circuit breaker state monitoring

## 📋 Migration Plan

### Step 1: Run Database Migration
```bash
cd backend/services/task_service
docker-compose exec task-service alembic upgrade head
```

### Step 2: Test Pantheon Connection
```bash
# Test authentication
curl -X POST http://109.72.96.136:3003/login \
  -H "Content-Type: application/json" \
  -d '{"username": "CunguDeklaracije", "password": "0778657825"}'

# Test getIdentWMS (with token)
curl -X GET "http://109.72.96.136:3003/getIdentWMS?limit=10" \
  -H "Authorization: Bearer <token>"
```

### Step 3: Initial Catalog Sync
```bash
# Trigger first sync via API (once Phase 6 is complete)
curl -X POST http://localhost:5000/api/sync/catalog \
  -H "Authorization: Bearer <admin_token>"
```

### Step 4: Schedule Cron Jobs
```yaml
# Catalog: Daily at 02:00
0 2 * * * curl -X POST http://localhost:5000/api/sync/catalog

# Subjects: Daily at 02:30
30 2 * * * curl -X POST http://localhost:5000/api/sync/subjects

# Issue Docs: Every 2 hours
0 */2 * * * curl -X POST http://localhost:5000/api/sync/issue

# Receipt Docs: Every 2 hours (offset 30min)
30 */2 * * * curl -X POST http://localhost:5000/api/sync/receipt
```

## 🎯 Definition of Done (DoD)

- [ ] Catalog + subjects delta sync runs nightly, Admin shows real data
- [ ] Real issue/receipt docs imported, only `exists_in_wms = true` visible in WMS
- [ ] Worker can complete partial tasks with reason, Admin reflects it
- [ ] No duplicate imports; idempotent sync
- [ ] Rate-limit + retry logic verified stable
- [ ] PWA + TV show live shift/team metrics
- [ ] All docs updated (catalog-sync.md, subjects-sync.md, import-pipeline.md, runbook.md)

## 📊 Current Progress: 30% Complete (3/10 Phases)

**Next Steps:**
1. Complete Phase 3 (Catalog Sync Service) - Add API endpoint
2. Implement Phase 4 (Subjects Sync)
3. Implement Phase 5 (Document Import with exists_in_wms logic)
4. Then UI updates and testing

## 🚀 Quick Start (Once Complete)

1. Set environment variables in `.env` or `docker-compose.yml`
2. Run migrations: `alembic upgrade head`
3. Trigger initial syncs via Admin UI
4. Monitor Prometheus metrics
5. Verify data in Admin pages (Catalog, Subjects, Documents)
6. Test PWA with real user accounts

