# Cycle Counting (Popis magacina)

## Overview

Cycle Counting is a periodic inventory accuracy verification process that ensures system quantities match physical stock, based on Manhattan Active WMS best practices.

## Purpose

- **Maintain inventory accuracy** (target: > 95%)
- **Detect discrepancies** early (before they impact operations)
- **Continuous improvement** (identify root causes)
- **Regulatory compliance** (audit trail)

---

## Cycle Count Types

### 1. Zone Count
- Count all bins in a zone
- **Use case:** Weekly zone rotation
- **Duration:** 2-4 hours
- **Example:** All bins in "Zona A"

### 2. Regal Count
- Count all bins in a regal/aisle
- **Use case:** Daily spot checks
- **Duration:** 30-60 min
- **Example:** All bins in "Regal A1"

### 3. Article Count
- Count specific article across all locations
- **Use case:** High-value or fast-moving items
- **Duration:** 15-30 min
- **Example:** Article "ART001" in all bins

### 4. Random Count (ABC Analysis)
- Random selection of 10 items
- **Use case:** Daily random sampling
- **Duration:** 20-30 min
- **Strategy:** Prioritize slow-movers and high-value

---

## Cycle Count Workflow

### 1. Create Cycle Count (Admin/Šef)

**API Endpoint:**
```http
POST /api/locations/cycle-counts
Authorization: Bearer <token>
Content-Type: application/json

{
  "location_id": "uuid",  // Or null for article/random
  "count_type": "zone",   // zone, regal, article, random
  "scheduled_at": "2025-10-20T08:00:00Z",
  "assigned_to_id": "uuid"  // Optional: assign to worker
}
```

**Response:**
```json
{
  "id": "uuid",
  "location_code": "ZA",
  "count_type": "zone",
  "scheduled_at": "2025-10-20T08:00:00Z",
  "status": "scheduled",
  "items": [
    {
      "id": "uuid",
      "artikal_sifra": "ART001",
      "artikal_naziv": "Proizvod 1",
      "location_code": "ZA-R01-P01-B01",
      "system_quantity": 100
    },
    // ... all items in scope
  ]
}
```

### 2. Start Cycle Count (Worker - PWA)

**API Endpoint:**
```http
POST /api/locations/cycle-counts/{id}/start
Authorization: Bearer <token>
```

- Sets status to "in_progress"
- Records `started_at` timestamp
- Assigns to current user

### 3. Count Items (PWA)

**UI Features:**
- **One-item-at-a-time focus**
- Progress bar (X / Y prebrojano)
- Item details (code, name, location)
- System quantity display
- **Large number input** (24px font)
- **Quick actions:**
  - "= Sistem" (matches system)
  - "0 (Nema)" (zero quantity)

**Variance Detection:**
- **Positive variance (Višak):** counted > system
- **Negative variance (Manjak):** counted < system
- **Color coding:**
  - Green: Višak
  - Red: Manjak
  - Orange: Warning (> 5% deviation)

**Reason Input:**
- Required if variance > 5%
- Free text field
- Common reasons:
  - "Vraćena roba"
  - "Oštećenje u skladištu"
  - "Greška pri prijemu"
  - "Artikal premešten"

### 4. Complete Cycle Count

**API Endpoint:**
```http
POST /api/locations/cycle-counts/{id}/complete
Authorization: Bearer <token>
Content-Type: application/json

{
  "counts": [
    {
      "item_id": "uuid",
      "counted_quantity": 98,
      "reason": "2 komada oštećeno"
    },
    // ... all items
  ]
}
```

**Process:**
1. Update each item with counted quantity
2. Calculate variance (counted - system)
3. Calculate variance % (variance / system * 100)
4. Mark items with `is_discrepancy` if variance ≠ 0
5. Mark items with `requires_recount` if variance > 5%
6. **Adjust inventory** in `article_locations`
7. Update location capacity
8. Calculate accuracy percentage
9. Set status to "completed"

**Response:**
```json
{
  "id": "uuid",
  "status": "completed",
  "accuracy_percentage": 96.5,
  "completed_at": "2025-10-20T10:30:00Z",
  "items": [
    {
      "artikal_sifra": "ART001",
      "system_quantity": 100,
      "counted_quantity": 98,
      "variance": -2,
      "variance_percent": -2.0,
      "is_discrepancy": true,
      "requires_recount": false,
      "reason": "2 komada oštećeno"
    }
  ]
}
```

---

## Database Schema

### `cycle_counts` Table
```sql
CREATE TABLE cycle_counts (
    id UUID PRIMARY KEY,
    location_id UUID REFERENCES locations(id),
    scheduled_at TIMESTAMP WITH TIME ZONE NOT NULL,
    assigned_to_id UUID REFERENCES users(id),
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    status cycle_count_status_enum DEFAULT 'scheduled',  -- scheduled, in_progress, completed, cancelled
    count_type VARCHAR(32),  -- zone, regal, article, random
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### `cycle_count_items` Table
```sql
CREATE TABLE cycle_count_items (
    id UUID PRIMARY KEY,
    cycle_count_id UUID REFERENCES cycle_counts(id) ON DELETE CASCADE,
    artikal_id UUID REFERENCES artikal(id) NOT NULL,
    location_id UUID REFERENCES locations(id) NOT NULL,
    system_quantity NUMERIC(12,3) NOT NULL,
    counted_quantity NUMERIC(12,3),
    variance NUMERIC(12,3),
    variance_percent NUMERIC(5,2),
    reason VARCHAR(255),
    counted_by_id UUID REFERENCES users(id),
    counted_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Variance Thresholds

### Alert Levels

| Variance | Action | Alert |
|----------|--------|-------|
| 0% | ✅ Match | None |
| 0.1-5% | ℹ️ Minor | Info |
| 5-10% | ⚠️ Moderate | Warning |
| > 10% | ❌ Major | Recount required |

### Automatic Actions

- **Match (0%):** No action, inventory confirmed
- **Minor (< 5%):** Adjust inventory, log variance
- **Moderate (5-10%):** Adjust + require reason
- **Major (> 10%):** Require recount + supervisor approval

---

## Metrics & KPIs

### Accuracy Metrics
- **Accuracy percentage:** (items_match / total_items) * 100
- **Target:** > 95%
- **Critical:** < 90% requires investigation

### Discrepancy Analysis
- **Discrepancy rate:** items_with_variance / total_items
- **Avg variance:** sum(variance) / items_with_variance
- **Top 5 reasons** for variance

### Operational Metrics
- **Counts per day:** Target 5-10
- **Avg count duration:** Target < 30 min
- **Items counted per hour:** Target > 40

### Trend Analysis
- **Monthly accuracy trend**
- **Discrepancy by zone**
- **Discrepancy by article class**
- **Variance by worker** (training indicator)

---

## Admin UI (Popis razlike - Discrepancy Report)

### Cycle Counts List
- Filter by status (scheduled, in_progress, completed)
- Filter by assigned worker
- Columns:
  - Location/Zone
  - Count type
  - Scheduled date
  - Status badge
  - Accuracy %
  - Discrepancies count
  - Actions (View, Cancel)

### Cycle Count Detail
- Header: Location, type, dates
- Accuracy percentage (color-coded)
- Items table:
  - Article code & name
  - Location
  - System qty
  - Counted qty
  - Variance (+ & -)
  - Variance %
  - Reason
  - Counted by/at
- Export to CSV/PDF

### Discrepancy Report
- Filter by date range, zone, article
- Grouping: by article, by location, by worker
- Charts:
  - Accuracy trend (line chart)
  - Discrepancies by zone (bar chart)
  - Top 5 reasons (pie chart)
- Export to Excel

---

## RBAC Access Control

| Role | Create | Start | Count | Complete | Cancel | View Reports |
|------|--------|-------|-------|----------|--------|--------------|
| ADMIN | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| MENADŽER | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| ŠEF | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| MAGACIONER | ❌ | ✅ | ✅ | ✅ | ❌ | ❌ |
| KOMERCIJALISTA | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

---

## Best Practices

### Scheduling
- **Daily:** Random counts (10 items)
- **Weekly:** Zone rotation (1 zone per week)
- **Monthly:** Full warehouse count
- **Ad-hoc:** High-value items quarterly

### Execution
- Count during low-activity periods (early morning)
- Assign to experienced workers
- Use barcode scanner for accuracy
- Verify high-variance items immediately

### Root Cause Analysis
- Track common variance reasons
- Train workers on proper procedures
- Investigate systematic issues
- Update processes to prevent recurrence

---

## Integration

- **Receiving:** Trigger count after large receipts
- **Picking:** Count empty bins before refill
- **Returns:** Count returned items
- **Damaged Goods:** Count and adjust immediately

---

## Testing

See `test-report-phase3.md` for:
- Cycle count creation tests (4 types)
- Variance calculation tests
- Inventory adjustment tests
- Accuracy percentage tests
- Discrepancy detection tests

