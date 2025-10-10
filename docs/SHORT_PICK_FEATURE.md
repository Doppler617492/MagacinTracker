# Short-Pick & SKU Scan Feature Documentation

## Overview

The Short-Pick & SKU Scan feature enables warehouse workers to record actual picked quantities, handle shortages, and complete documents even when items are missing or partially available. This feature bridges the gap between ideal warehouse operations and real-world scenarios.

## Business Problem

Traditional warehouse systems assume 100% inventory accuracy. In reality:
- Items may be missing from their designated locations
- Quantities may be less than requested (damaged, misplaced, etc.)
- Workers need to document shortages for inventory reconciliation
- Managers need visibility into shortage patterns

## Solution

A complete shortage tracking system that:
1. Allows workers to scan or manually enter SKUs
2. Records actual picked quantities (may be less than requested)
3. Captures shortage reasons for analysis
4. Enables document completion despite shortages
5. Provides comprehensive shortage reports for management

---

## Architecture

### Database Schema

#### New Enum: `discrepancy_status_enum`
```sql
CREATE TYPE discrepancy_status_enum AS ENUM (
    'none',          -- No shortage
    'short_pick',    -- Partial quantity picked
    'not_found',     -- Item not located
    'damaged',       -- Item damaged/unusable
    'wrong_barcode'  -- Barcode mismatch
);
```

#### Extended Tables

**`trebovanje_stavka` (Document Items)**
```sql
ALTER TABLE trebovanje_stavka ADD COLUMN
    picked_qty NUMERIC(12,3) DEFAULT 0,
    missing_qty NUMERIC(12,3) DEFAULT 0,
    discrepancy_status discrepancy_status_enum DEFAULT 'none',
    discrepancy_reason TEXT,
    last_scanned_code VARCHAR(64);
```

**`trebovanje` (Documents)**
```sql
ALTER TABLE trebovanje ADD COLUMN
    allow_incomplete_close BOOLEAN DEFAULT TRUE,
    closed_by UUID REFERENCES users(id),
    closed_at TIMESTAMP WITH TIME ZONE;
```

### API Endpoints

#### Worker Endpoints

**1. Catalog Lookup (Public)**
```http
GET /api/catalog/lookup?code={barcode_or_sku}

Response:
{
  "artikal_id": "uuid",
  "sifra": "12345",
  "naziv": "Article Name",
  "jedinica_mjere": "kom",
  "aktivan": true,
  "barkodovi": [
    {"value": "123456789", "is_primary": true}
  ]
}
```

**2. Pick by Code**
```http
POST /api/worker/tasks/{stavka_id}/pick-by-code

Body:
{
  "code": "12345",           // SKU or barcode
  "quantity": 5,
  "operation_id": "unique-id"
}

Response:
{
  "stavka_id": "uuid",
  "picked_qty": 5,
  "required_qty": 10,
  "missing_qty": 5,
  "discrepancy_status": "none",
  "needs_barcode": false,
  "matched_code": "12345",
  "message": "Picked 5. Total: 5/10"
}
```

**3. Record Short Pick**
```http
POST /api/worker/tasks/{stavka_id}/short-pick

Body:
{
  "actual_qty": 3,
  "reason": "Oštećeno",
  "operation_id": "unique-id"
}

Response:
{
  "stavka_id": "uuid",
  "picked_qty": 3,
  "required_qty": 10,
  "missing_qty": 7,
  "discrepancy_status": "short_pick",
  "message": "Short pick recorded: 3/10"
}
```

**4. Mark Not Found**
```http
POST /api/worker/tasks/{stavka_id}/not-found

Body:
{
  "reason": "Nema na lokaciji",
  "operation_id": "unique-id"
}

Response:
{
  "stavka_id": "uuid",
  "picked_qty": 0,
  "required_qty": 10,
  "discrepancy_status": "not_found",
  "message": "Item marked as not found"
}
```

**5. Complete Document**
```http
POST /api/worker/documents/{trebovanje_id}/complete

Body:
{
  "confirm_incomplete": true,
  "operation_id": "unique-id"
}

Response:
{
  "trebovanje_id": "uuid",
  "total_items": 15,
  "completed_items": 15,
  "items_with_shortages": 3,
  "total_shortage_qty": 12.5,
  "status": "done",
  "message": "Document completed with 3 shortage(s)"
}
```

#### Admin Endpoints

**6. Shortage Reports**
```http
GET /api/reports/shortages?from_date=2024-01-01&to_date=2024-12-31&format=json

Query Parameters:
- from_date: Start date (YYYY-MM-DD)
- to_date: End date (YYYY-MM-DD)
- radnja_id: Filter by store UUID
- magacioner_id: Filter by worker UUID
- discrepancy_status: Filter by status (short_pick, not_found, damaged)
- format: Output format (json or csv)

Response (JSON):
[
  {
    "trebovanje_dokument_broj": "25-20AT-000336",
    "trebovanje_datum": "2024-10-10 15:30",
    "radnja_naziv": "Radnja Budva",
    "magacin_naziv": "Transit Warehouse",
    "artikal_sifra": "12345",
    "artikal_naziv": "Test Artikal",
    "required_qty": 10,
    "picked_qty": 7,
    "missing_qty": 3,
    "discrepancy_status": "short_pick",
    "discrepancy_reason": "Oštećeno",
    "magacioner_name": "Gezim Maku",
    "completed_at": "2024-10-10 16:45"
  }
]
```

---

## User Workflows

### Worker Workflow (PWA)

#### 1. Scanning Flow
```
1. Worker opens task detail page
2. Clicks "Skeniraj" button on an item
3. Modal opens with barcode/SKU input
4. Worker scans barcode or enters SKU
5. System validates code matches item
   ✅ If match: NumPad opens for quantity
   ❌ If mismatch: Error shown
6. Worker enters quantity (max = remaining)
7. System records pick and updates progress
```

#### 2. Short-Pick Flow
```
1. Worker clicks "Djelimično" button
2. Modal opens asking for quantity
3. Worker enters partial quantity via NumPad
4. Worker selects reason from dropdown:
   - Nema na lokaciji
   - Oštećeno
   - Pogrešna lokacija
   - Nedovoljno zaliha
   - Ostalo
5. System records shortage
6. Item marked with warning indicator
```

#### 3. Not-Found Flow
```
1. Worker clicks "Nije pronađeno" button
2. Modal asks for reason (optional)
3. Worker confirms
4. System sets picked_qty = 0
5. Item marked as not_found
```

#### 4. Document Completion
```
1. Worker completes all items (or marks shortages)
2. Clicks "Završi dokument" button
3. If shortages exist:
   - Warning modal shown
   - Lists number of items with shortages
   - Requires explicit confirmation
4. Worker confirms
5. Document status → done
6. Shortage data synced to reports
```

### Manager Workflow (Admin)

#### Viewing Shortage Reports

**Navigation:** Admin → Manjkovi

**Features:**
- **Statistics Dashboard:**
  - Total items with shortages
  - Total missing quantity
  - Total required quantity
  - Shortage rate percentage

- **Filters:**
  - Date range picker
  - Discrepancy status dropdown
  - Store filter (future)
  - Worker filter (future)

- **Table Columns:**
  - Document number & date
  - Store & warehouse
  - SKU & article name
  - Required / Picked / Missing quantities
  - Status (color-coded)
  - Reason
  - Worker name
  - Completion timestamp

- **Export:**
  - CSV format
  - Excel-compatible
  - All filtered data included
  - Filename: `shortage_report_YYYYMMDD_HHMMSS.csv`

---

## Business Rules

### Validation Rules

1. **Quantity Validation:**
   - `picked_qty` ≤ `required_qty` (no overpick by default)
   - `missing_qty` = max(0, `required_qty` - `picked_qty`)
   - Quantities must be positive numbers

2. **Code Matching:**
   - Scanned code must match item's SKU or barcode
   - Lookup searches SKU first, then barcode
   - Mismatch results in error, no pick recorded

3. **Document Completion:**
   - All items must be processed (picked OR shortage marked)
   - If shortages exist, `confirm_incomplete` required
   - Without confirmation, completion is rejected

4. **Idempotency:**
   - All operations use `operation_id`
   - Duplicate operations with same ID are ignored
   - Critical for offline queue sync

### Status Transitions

**Item Status Flow:**
```
none (initial)
  ↓
[Scan/Pick] → none (if fully picked)
  ↓
[Partial]   → short_pick
  ↓
[Not Found] → not_found
  ↓
[Damaged]   → damaged
```

**Document Status Flow:**
```
new → assigned → in_progress → done
                              ↓
                         (with shortages)
```

---

## Offline Support

### Queue Mechanism

When offline, all operations are queued:

```typescript
interface OfflineAction {
  id: string;
  type: 'pick-by-code' | 'short-pick' | 'not-found' | 'complete-document';
  taskItemId: string;
  payload: any;
  timestamp: number;
  synced: boolean;
  retryCount: number;
}
```

**Sync Process:**
1. Worker performs action offline
2. Action added to IndexedDB queue
3. Visual indicator shows "Pending"
4. When online, queue automatically syncs
5. Each action processed with `operation_id`
6. Duplicates prevented by server

---

## Audit & Compliance

### Audit Events

All shortage operations generate audit logs:

```typescript
enum AuditAction {
  SCAN_OK = "SCAN_OK",
  SCAN_MISMATCH = "SCAN_MISMATCH",
  SHORT_PICK_RECORDED = "SHORT_PICK_RECORDED",
  NOT_FOUND_RECORDED = "NOT_FOUND_RECORDED",
  DOC_COMPLETED_INCOMPLETE = "DOC_COMPLETED_INCOMPLETE",
  LOOKUP_BY_CODE = "LOOKUP_BY_CODE"
}
```

**Audit Record Structure:**
```json
{
  "action": "SHORT_PICK_RECORDED",
  "user_id": "uuid",
  "timestamp": "2024-10-10T14:30:00Z",
  "resource_id": "stavka_uuid",
  "details": {
    "actual_qty": 3,
    "required_qty": 10,
    "missing_qty": 7,
    "reason": "Oštećeno",
    "operation_id": "unique-id"
  }
}
```

---

## Performance Considerations

### Database Indexes

Recommended indexes for optimal performance:

```sql
-- Shortage queries
CREATE INDEX idx_stavka_discrepancy ON trebovanje_stavka(discrepancy_status) 
WHERE discrepancy_status != 'none';

CREATE INDEX idx_stavka_missing ON trebovanje_stavka(missing_qty) 
WHERE missing_qty > 0;

-- Report queries
CREATE INDEX idx_trebovanje_closed ON trebovanje(closed_at DESC);
CREATE INDEX idx_trebovanje_closed_by ON trebovanje(closed_by);
```

### Caching Strategy

- **Catalog data:** Cached for 1 hour
- **Task data:** Refetched every 30 seconds
- **Shortage reports:** No cache (always fresh)

---

## Analytics & KPIs

### Key Metrics

1. **Shortage Rate:**
   ```
   (Total Missing Qty / Total Required Qty) × 100
   ```

2. **Items with Shortages:**
   ```
   COUNT(items WHERE missing_qty > 0 OR discrepancy_status != 'none')
   ```

3. **Top Shortage Reasons:**
   ```sql
   SELECT discrepancy_reason, COUNT(*) 
   FROM trebovanje_stavka 
   WHERE discrepancy_status != 'none'
   GROUP BY discrepancy_reason
   ORDER BY COUNT(*) DESC;
   ```

4. **Worker Performance:**
   ```sql
   SELECT 
     closed_by,
     COUNT(*) as documents_completed,
     SUM(CASE WHEN items_with_shortages > 0 THEN 1 ELSE 0 END) as with_shortages,
     AVG(missing_qty) as avg_shortage
   FROM trebovanje
   GROUP BY closed_by;
   ```

---

## Testing Guide

### Manual Test Scenarios

#### Scenario 1: Normal Pick Flow
```
1. Login as worker (gezim.maku@cungu.com / Worker123!)
2. Open task "25-20AT-000336"
3. Click "Skeniraj" on first item
4. Enter correct SKU
5. Enter quantity (e.g., 5)
✅ Verify: Progress bar updates, item shows 5/10
```

#### Scenario 2: Code Mismatch
```
1. Click "Skeniraj" on item
2. Enter wrong SKU (e.g., "99999")
✅ Verify: Error message "Code not found in catalog"
3. Enter SKU from different item
✅ Verify: Error message "Scanned item does not match expected item"
```

#### Scenario 3: Short Pick
```
1. Click "Djelimično" on item
2. Enter partial quantity (e.g., 3 out of 10)
3. Select reason: "Oštećeno"
4. Confirm
✅ Verify: Item shows warning, reason displayed, missing_qty = 7
```

#### Scenario 4: Not Found
```
1. Click "Nije pronađeno"
2. Select reason: "Nema na lokaciji"
3. Confirm
✅ Verify: Item marked red, picked_qty = 0, status = not_found
```

#### Scenario 5: Complete with Shortages
```
1. Process all items (mix of picks and shortages)
2. Click "Završi dokument"
✅ Verify: Warning modal shown with shortage count
3. Confirm completion
✅ Verify: Redirected to task list, document marked done
```

#### Scenario 6: Admin Reports
```
1. Login as admin (admin@magacin.com / Admin123!)
2. Navigate to "Manjkovi" page
3. Select date range
4. Filter by status: "short_pick"
5. Click "Preuzmi CSV"
✅ Verify: CSV downloads with correct data
```

### API Testing with cURL

**Test Catalog Lookup:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/catalog/lookup?code=12345"
```

**Test Pick by Code:**
```bash
curl -X POST \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"12345","quantity":5,"operation_id":"test-001"}' \
  "http://localhost:8123/api/worker/tasks/{stavka_id}/pick-by-code"
```

**Test Shortage Report:**
```bash
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/reports/shortages?format=json&from_date=2024-01-01"
```

---

## Troubleshooting

### Common Issues

**1. "Code not found in catalog"**
- **Cause:** SKU/barcode not in `artikal` table
- **Solution:** Run catalog enrichment or manually add article

**2. "Scanned item does not match expected item"**
- **Cause:** Worker scanned wrong item's code
- **Solution:** Verify correct item, scan again

**3. "Cannot complete document - confirm_incomplete required"**
- **Cause:** Shortages exist but not explicitly confirmed
- **Solution:** Set `confirm_incomplete: true` in request

**4. Offline actions not syncing**
- **Cause:** Network reconnected but queue not processing
- **Solution:** Check browser console, verify `operation_id` uniqueness

**5. CSV export empty**
- **Cause:** No shortages in selected date range
- **Solution:** Adjust filters, verify data exists

---

## Security & RBAC

### Role Permissions

| Endpoint | Worker | Šef | Menadžer | Admin |
|----------|--------|-----|----------|-------|
| Catalog Lookup | ✅ | ✅ | ✅ | ✅ |
| Pick by Code | ✅ | ✅ | ❌ | ❌ |
| Short Pick | ✅ | ✅ | ❌ | ❌ |
| Not Found | ✅ | ✅ | ❌ | ❌ |
| Complete Doc | ✅ | ✅ | ❌ | ❌ |
| Shortage Reports | ❌ | ✅ | ✅ | ✅ |

### Data Privacy

- Workers only see their assigned tasks
- Managers see all shortages in their region
- Personal data (reasons, worker names) included in exports
- Audit logs retain indefinitely for compliance

---

## Future Enhancements

### Planned Features

1. **Photo Documentation:**
   - Allow workers to attach photos of damaged items
   - Store in S3/MinIO
   - Display in shortage reports

2. **Barcode Generation:**
   - Auto-generate barcodes for items without them
   - Print labels via Zebra printer API

3. **AI-Powered Predictions:**
   - Predict shortage likelihood based on historical data
   - Recommend optimal picking routes

4. **Real-Time Notifications:**
   - Alert managers when shortage rate exceeds threshold
   - Slack/Email integration

5. **Inventory Adjustments:**
   - Auto-create inventory adjustment documents
   - Sync with ERP (Pantheon)

6. **Mobile App:**
   - Native iOS/Android app
   - Better camera integration
   - Push notifications

---

## Appendix

### Database Migration

**File:** `backend/services/task_service/alembic/versions/003_add_shortage_tracking.py`

**Apply:**
```bash
docker compose exec task-service alembic upgrade head
```

**Rollback:**
```bash
docker compose exec task-service alembic downgrade -1
```

### Configuration

**Environment Variables:**
```env
# Enable/disable shortage tracking
FEATURE_SHORTAGE_TRACKING=true

# Default quantity cap behavior
ALLOW_OVERPICK=false

# Offline queue retention (days)
OFFLINE_QUEUE_RETENTION_DAYS=30

# Report export limits
MAX_SHORTAGE_EXPORT_ROWS=10000
```

### API Rate Limits

- Catalog lookup: 100 req/min per user
- Pick operations: 60 req/min per user
- Reports: 10 req/min per user
- CSV export: 2 req/min per user

---

## Support & Contact

**Technical Issues:**
- Check logs: `docker compose logs task-service`
- Database issues: `docker compose logs db`
- Frontend issues: Browser DevTools Console

**Feature Requests:**
- Open GitHub issue
- Email: support@magacin.com

**Training:**
- Video tutorials: /docs/videos/
- User manual: /docs/USER_MANUAL.md

---

## Changelog

### Version 0.3.0 (2024-10-10)
- ✅ Initial release of Short-Pick & SKU Scan feature
- ✅ Database schema with shortage tracking
- ✅ 7 new API endpoints
- ✅ PWA worker interface redesign
- ✅ Admin shortage reports page
- ✅ Offline queue support
- ✅ Comprehensive audit logging
- ✅ CSV export functionality

---

**Document Version:** 1.0  
**Last Updated:** 2024-10-10  
**Author:** AI Development Team  
**Status:** ✅ Production Ready

