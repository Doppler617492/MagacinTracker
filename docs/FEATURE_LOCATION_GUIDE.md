# Feature Location Guide - Where to Find Everything

This guide shows you exactly where each feature is located in the application and how to access it.

---

## 🎯 Quick Access Map

### For Workers (PWA - http://localhost:5131)

| Feature | Location | How to Access |
|---------|----------|---------------|
| **Shortage Tracking** | Task Detail Page | Click any task → Scan/Pick items |
| **Barcode Scanning** | Task Item | Click "Skeniraj" button |
| **SKU Entry** | Task Item | Click "Skeniraj" → Type SKU |
| **Quantity Entry** | NumPad Modal | After scanning → Enter quantity |
| **Short Pick** | Task Item | Click "Djelimično" button |
| **Not Found** | Task Item | Click "Nije pronađeno" button |
| **Document Completion** | Task Detail Bottom | Click "Završi dokument" button |
| **Offline Queue** | Automatic | Works transparently when offline |

### For Managers (Admin - http://localhost:5130)

| Feature | Location | How to Access |
|---------|----------|---------------|
| **Shortage Reports** | Navigation Menu | Click "Manjkovi" in top menu |
| **Statistics Dashboard** | Shortage Reports Page | Top 4 cards (auto-loads) |
| **Date Filtering** | Shortage Reports | Use date range picker |
| **Status Filtering** | Shortage Reports | Select from dropdown |
| **CSV Export** | Shortage Reports | Click "Preuzmi CSV" button |
| **Shortage Details** | Shortage Reports | Scrollable table with all data |

---

## 📱 PWA Worker Interface (Port 5131)

### Login Page
**URL:** `http://localhost:5131/login`

**Credentials:**
- Email: `gezim.maku@cungu.com`
- Password: `Worker123!`

### Home Page (Task List)
**URL:** `http://localhost:5131/`

**What You See:**
- Header with warehouse name, user info, status icons
- AI Insights panel (if predictions available)
- "MOJI ZADACI" section
- List of task cards with:
  - Document number
  - Location
  - Progress (X/Y stavki)
  - Status badge
  - "Otvori zadatak" button

**Navigation:**
- Bottom bar: Home | Zadaci | Izvještaji | Postavke

### Task Detail Page ⭐ (NEW SHORTAGE FEATURES)
**URL:** `http://localhost:5131/tasks/{task_id}`

#### Header Section
- **Document Number:** e.g., "25-20AT-000336"
- **Location:** e.g., "Transit Warehouse - Budva 2"
- **Status Tag:** Assigned / U toku / Završen

#### Progress Section
- **Progress Bar:** Visual completion percentage
- **Stats:** "X / Y stavki" (completed/total)

#### Shortage Warning (if applicable)
- **Orange alert box:** "N stavke sa manjkom"
- **Message:** "Dokumentuj razlog prije završetka"

#### Item Cards
Each item shows:

**Header:**
- Article name (bold)
- SKU code (gray)
- Status icon (check or warning)

**Progress Bar:**
- Current: picked_qty / required_qty
- Color: Green (complete) | Orange (shortage) | Blue (in progress)

**Shortage Info (if applicable):**
- Status label: "Djelimično prikupljeno" / "Nije pronađeno"
- Reason text
- Missing quantity

**Action Buttons (when item not complete):**

1. **"Skeniraj" Button (Blue):**
   - Opens scan modal
   - Enter barcode or SKU
   - Click "Nastavi"
   - NumPad opens for quantity
   - System validates code

2. **"Djelimično" Button (Gray):**
   - Opens NumPad directly
   - Enter partial quantity
   - Select reason from dropdown:
     * Nema na lokaciji
     * Oštećeno
     * Pogrešna lokacija
     * Nedovoljno zaliha
     * Ostalo
   - Records shortage

3. **"Nije pronađeno" Button (Small, bottom):**
   - Opens reason modal
   - Select optional reason
   - Confirms item not found
   - Sets picked_qty = 0

#### Complete Document Section (Bottom, Fixed)
- **Green Button:** "Završi dokument"
- **Enabled:** When all items processed
- **Click:** Opens confirmation modal if shortages exist
- **Confirms:** "Da li želite završiti dokument sa evidentiranim manjkovima?"

#### Modals

**1. Scan Modal:**
```
Title: "Skeniraj barkod ili unesi SKU"
Content:
  - Article name
  - SKU code
  - Input field (with barcode icon)
  - "Nastavi" button
```

**2. NumPad Modal:**
```
Title: "Unesite količinu"
Display: Large number (48px font)
Hint: "Maksimum: X"
Grid: 3x4 numeric keypad
  [7] [8] [9]
  [4] [5] [6]
  [1] [2] [3]
  [C] [0] [.]
Actions:
  - [Obriši] button
  - [Otkaži] [Potvrdi] buttons
```

**3. Shortage Modal:**
```
Title: "Djelimično prikupljanje" / "Označi kao nije pronađeno"
Content:
  - Article details
  - [Unesi prikupljenu količinu] button (for short-pick)
  - Reason dropdown
  - [Potvrdi] button
```

**4. Completion Confirmation Modal:**
```
Title: "Potvrdi završetak"
Warning: "⚠️ Dokument ima N stavke sa manjkom"
Message: "Da li želite završiti dokument sa evidentiranim manjkovima?"
Actions: [Otkaži] [Potvrdi završetak]
```

---

## 🖥️ Admin Interface (Port 5130)

### Login Page
**URL:** `http://localhost:5130/login`

**Credentials:**
- Email: `admin@magacin.com`
- Password: `Admin123!`

### Navigation Menu (Top Bar)
Located in dark header, horizontally scrollable:

```
Dashboard | Trebovanja | Scheduler | Katalog | Uvoz | Analitika | 
Izvještaji | Manjkovi ⭐ | AI Preporuke | AI Modeli | Global AI Hub | 
Live Ops | Global Ops | Korisnici
```

### Shortage Reports Page ⭐ (NEW)
**URL:** `http://localhost:5130/shortages`
**Menu:** Click "Manjkovi" (has WarningOutlined icon)

#### Statistics Cards (Top Row)
4 cards showing real-time KPIs:

**Card 1: Ukupno stavki sa manjkom**
- Icon: Warning triangle
- Value: Total count
- Color: Default

**Card 2: Ukupno nedostaje**
- Suffix: "kom"
- Value: Sum of missing_qty
- Color: Red

**Card 3: Ukupno traženo**
- Suffix: "kom"
- Value: Sum of required_qty
- Color: Default

**Card 4: Stopa manjka**
- Suffix: "%"
- Value: (missing/required) × 100
- Color: Green (<5%) | Red (>5%)

#### Filter Panel (Card)
White card with filters:

**1. Date Range Picker:**
- Start date input: "Datum od"
- End date input: "Datum do"
- Format: DD.MM.YYYY
- Click to open calendar

**2. Status Dropdown:**
- Placeholder: "Status manjka"
- Options:
  * Djelimično prikupljeno (short_pick)
  * Nije pronađeno (not_found)
  * Oštećeno (damaged)
- Clearable with X button

**3. Action Buttons:**
- **"Pretraži":** Refresh data with filters
- **"Preuzmi CSV":** Export filtered results

#### Data Table

**Columns (scrollable horizontally):**

| Column | Width | Content |
|--------|-------|---------|
| Dokument | 150px | Document number (fixed left) |
| Datum | 150px | Date + time |
| Radnja | 150px | Store name |
| Skladište | 150px | Warehouse name |
| Šifra | 120px | Article SKU |
| Artikal | 250px | Article name |
| Traženo | 100px | Required quantity (right-aligned) |
| Prikupljeno | 110px | Picked quantity (right-aligned) |
| Nedostaje | 110px | Missing quantity (red if >0, right-aligned) |
| Status | 150px | Color-coded tag with icon |
| Razlog | 200px | Shortage reason or "-" |
| Radnik | 150px | Worker full name |
| Završeno | 150px | Completion timestamp or "-" |

**Status Tags:**
- 🟠 Djelimično (orange) - short_pick
- 🔴 Nije pronađeno (red) - not_found  
- 🔥 Oštećeno (volcano) - damaged

**Pagination:**
- Page size: 50 rows
- Size changer: Yes
- Total count: "Ukupno X stavki"

#### CSV Export
**Triggered by:** "Preuzmi CSV" button
**Filename:** `shortage_report_YYYYMMDD_HHMMSS.csv`
**Format:** Excel-compatible, UTF-8
**Columns:** Same as table, all filtered data included

---

## 🔧 Backend API Endpoints

### Base URL: `http://localhost:8123/api`

### Catalog Endpoints

#### Lookup by Code
```
GET /catalog/lookup?code={barcode_or_sku}
Auth: Bearer token (any authenticated user)
Location: backend/services/task_service/app/routers/worker_picking.py:34
```

### Worker Picking Endpoints

#### Pick by Code
```
POST /worker/tasks/{stavka_id}/pick-by-code
Auth: Bearer token (worker/sef)
Location: backend/services/task_service/app/routers/worker_picking.py:47
```

#### Short Pick
```
POST /worker/tasks/{stavka_id}/short-pick
Auth: Bearer token (worker/sef)
Location: backend/services/task_service/app/routers/worker_picking.py:76
```

#### Not Found
```
POST /worker/tasks/{stavka_id}/not-found
Auth: Bearer token (worker/sef)
Location: backend/services/task_service/app/routers/worker_picking.py:103
```

#### Complete Document
```
POST /worker/documents/{trebovanje_id}/complete
Auth: Bearer token (worker/sef)
Location: backend/services/task_service/app/routers/worker_picking.py:130
```

### Admin Report Endpoints

#### Shortage Report
```
GET /reports/shortages?from_date=&to_date=&format=json|csv
Auth: Bearer token (sef/menadzer)
Location: backend/services/task_service/app/routers/reports.py:31
```

---

## 📂 Source Code Locations

### Backend Files

#### Database Schema
```
backend/services/task_service/alembic/versions/
  └─ 003_add_shortage_tracking.py (Migration)

backend/services/task_service/app/models/
  ├─ enums.py (Line 61-66: DiscrepancyStatus enum)
  ├─ enums.py (Line 93-99: Audit actions)
  └─ trebovanje.py (Lines 32-34, 68-74: New fields)
```

#### Business Logic
```
backend/services/task_service/app/services/
  ├─ shortage.py (NEW - 330 lines)
  │   ├─ ShortageService class
  │   ├─ pick_by_code() method (Line 37)
  │   ├─ record_short_pick() method (Line 122)
  │   ├─ record_not_found() method (Line 175)
  │   └─ complete_document() method (Line 214)
  │
  └─ catalog.py (Lines 255-302)
      └─ lookup() method (Extended for barcode search)
```

#### API Routers
```
backend/services/task_service/app/routers/
  ├─ worker_picking.py (NEW - 155 lines)
  │   ├─ lookup_by_code() endpoint
  │   ├─ pick_by_code() endpoint
  │   ├─ short_pick() endpoint
  │   ├─ not_found() endpoint
  │   └─ complete_document() endpoint
  │
  ├─ reports.py (NEW - 172 lines)
  │   └─ get_shortage_report() endpoint
  │
  └─ internal_catalog.py (Lines 47-58)
      └─ lookup_catalog_item() endpoint (Updated)
```

#### Schemas
```
backend/services/task_service/app/schemas/
  ├─ shortage.py (NEW - 83 lines)
  │   ├─ PickByCodeRequest
  │   ├─ PickByCodeResponse
  │   ├─ ShortPickRequest
  │   ├─ ShortPickResponse
  │   ├─ NotFoundRequest
  │   ├─ NotFoundResponse
  │   ├─ CompleteDocumentRequest
  │   ├─ CompleteDocumentResponse
  │   └─ ShortageReportItem
  │
  └─ __init__.py (Lines 55-65, 118-127: Exports)
```

### Frontend PWA Files

#### Components
```
frontend/pwa/src/components/
  └─ NumPad.tsx (NEW - 352 lines)
      ├─ NumPad component
      ├─ Touch-optimized number grid
      ├─ Large buttons (70px height)
      └─ Quantity validation
```

#### Pages
```
frontend/pwa/src/pages/
  └─ TaskDetailPage.tsx (REWRITTEN - 680 lines)
      ├─ Scan modal (Line 570)
      ├─ NumPad integration (Line 617)
      ├─ Shortage modal (Line 631)
      ├─ Completion modal (Line 672)
      ├─ Pick handlers (Lines 155-282)
      └─ UI rendering (Lines 295-680)
```

#### Utilities
```
frontend/pwa/src/lib/
  └─ offlineQueue.ts (Line 39: Updated action types)
```

#### Theme
```
frontend/pwa/src/
  └─ theme.ts (Lines 40-47: Spacing configuration)
```

### Frontend Admin Files

#### Pages
```
frontend/admin/src/pages/
  ├─ ShortageReportsPage.tsx (NEW - 370 lines)
  │   ├─ Statistics cards (Lines 70-95)
  │   ├─ Filter panel (Lines 135-163)
  │   ├─ Data table (Lines 172-283)
  │   └─ CSV export (Lines 33-65)
  │
  └─ App.tsx (Modified)
      ├─ Import (Line 33)
      ├─ Route (Line 172)
      ├─ Menu item (Lines 80-83)
      └─ Icon import (Line 18)
```

---

## 🗺️ User Journey Maps

### Worker: Scanning & Picking

```
Start
  ↓
Login (gezim.maku@cungu.com)
  ↓
Home Page (Task List)
  ↓
Click Task Card
  ↓
Task Detail Page
  ↓
See Item Cards
  ↓
Click "Skeniraj" on Item 1
  ↓
Scan Modal Opens
  ↓
Enter SKU: "12345"
  ↓
Click "Nastavi"
  ↓
NumPad Opens
  ↓
Enter Quantity: 5
  ↓
Click "Potvrdi"
  ↓
✅ Pick Recorded
  ↓
Progress Bar Updates (5/10)
  ↓
Repeat for Other Items
  ↓
All Items Done
  ↓
Click "Završi dokument"
  ↓
✅ Task Complete
```

### Worker: Handling Shortage

```
Task Detail Page
  ↓
Item Can't Be Found
  ↓
Click "Nije pronađeno"
  ↓
Shortage Modal Opens
  ↓
Select Reason: "Nema na lokaciji"
  ↓
Click "Potvrdi - nije pronađeno"
  ↓
✅ Shortage Recorded
  ↓
Item Marked Red
  ↓
Warning Badge Shows
  ↓
Continue with Other Items
  ↓
Click "Završi dokument"
  ↓
⚠️ Confirmation Modal
  ↓
"Dokument ima 1 stavku sa manjkom"
  ↓
Click "Potvrdi završetak"
  ↓
✅ Task Complete with Shortages
```

### Manager: Viewing Shortage Report

```
Start
  ↓
Login (admin@magacin.com)
  ↓
Dashboard Loads
  ↓
Click "Manjkovi" in Menu
  ↓
Shortage Reports Page
  ↓
See Statistics:
  - 15 items with shortages
  - 45 kom missing
  - 500 kom required
  - 9% shortage rate
  ↓
Set Date Range: Last 7 days
  ↓
Select Status: "Djelimično prikupljeno"
  ↓
Click "Pretraži"
  ↓
Table Refreshes
  ↓
See 8 Filtered Results
  ↓
Review Details:
  - Which items
  - Which workers
  - What reasons
  ↓
Click "Preuzmi CSV"
  ↓
✅ Excel File Downloads
  ↓
Open in Excel
  ↓
Analyze Data
```

---

## 🔍 Quick Search Guide

### "How do I find..."

**Q: Where do workers scan barcodes?**
A: PWA → Open Task → Click "Skeniraj" button on any item

**Q: How do workers enter quantities?**
A: After scanning, NumPad modal opens automatically

**Q: Where can I see shortage reasons?**
A: Admin → Manjkovi → "Razlog" column in table

**Q: How do I export shortage data?**
A: Admin → Manjkovi → "Preuzmi CSV" button

**Q: Where are offline actions queued?**
A: Automatic - stored in IndexedDB, syncs when online

**Q: How do I check if a code is valid?**
A: API: GET /catalog/lookup?code=12345

**Q: Where is the NumPad component code?**
A: `frontend/pwa/src/components/NumPad.tsx`

**Q: How do I see audit logs?**
A: Database: `SELECT * FROM audit_log WHERE action LIKE '%SHORTAGE%'`

**Q: Where is the shortage business logic?**
A: `backend/services/task_service/app/services/shortage.py`

**Q: How do I test shortage tracking?**
A: See `docs/SHORT_PICK_FEATURE.md` → Testing Guide

---

## 📊 Database Query Examples

### Find all shortages in last 7 days
```sql
SELECT 
  t.dokument_broj,
  ts.naziv,
  ts.required_qty,
  ts.picked_qty,
  ts.missing_qty,
  ts.discrepancy_status,
  ts.discrepancy_reason,
  u.first_name || ' ' || u.last_name as worker
FROM trebovanje_stavka ts
JOIN trebovanje t ON ts.trebovanje_id = t.id
LEFT JOIN users u ON t.closed_by = u.id
WHERE ts.discrepancy_status != 'none'
  AND t.datum >= NOW() - INTERVAL '7 days'
ORDER BY t.datum DESC;
```

### Calculate shortage rate by worker
```sql
SELECT 
  u.first_name || ' ' || u.last_name as worker,
  COUNT(*) as total_items,
  SUM(CASE WHEN ts.discrepancy_status != 'none' THEN 1 ELSE 0 END) as items_with_shortage,
  SUM(ts.missing_qty) as total_missing,
  SUM(ts.kolicina_trazena) as total_required,
  ROUND((SUM(ts.missing_qty) / SUM(ts.kolicina_trazena) * 100)::numeric, 2) as shortage_rate_percent
FROM trebovanje t
JOIN trebovanje_stavka ts ON ts.trebovanje_id = t.id
LEFT JOIN users u ON t.closed_by = u.id
WHERE t.closed_at IS NOT NULL
GROUP BY u.id, u.first_name, u.last_name
ORDER BY shortage_rate_percent DESC;
```

### Find items most frequently not found
```sql
SELECT 
  ts.artikl_sifra,
  ts.naziv,
  COUNT(*) as not_found_count,
  ARRAY_AGG(DISTINCT ts.discrepancy_reason) as reasons
FROM trebovanje_stavka ts
WHERE ts.discrepancy_status = 'not_found'
GROUP BY ts.artikl_sifra, ts.naziv
HAVING COUNT(*) > 5
ORDER BY not_found_count DESC
LIMIT 20;
```

---

## 🎬 Video Walkthrough Timestamps

*(Create video and add timestamps here)*

- 00:00 - Introduction
- 01:30 - Worker Login
- 02:15 - Opening a Task
- 03:00 - Scanning Barcode
- 04:30 - Using NumPad
- 06:00 - Recording Short Pick
- 08:15 - Marking Not Found
- 10:00 - Completing with Shortages
- 12:30 - Admin Reports
- 15:00 - Filtering Data
- 17:00 - CSV Export
- 19:00 - Analytics & Insights

---

## 📞 Support Contacts

**Bug Reports:** GitHub Issues
**Feature Requests:** Product Team
**Training:** training@magacin.com
**Technical Support:** tech@magacin.com

---

**Last Updated:** 2024-10-10  
**Version:** 1.0  
**Maintained By:** Development Team

