# Magacin Track - User Guide

## Table of Contents
1. [For Workers](#for-workers)
2. [For Managers](#for-managers)
3. [Common Tasks](#common-tasks)
4. [Troubleshooting](#troubleshooting)

---

## For Workers

### Getting Started

**Device:** Zebra TC21 or TC26 handheld
**App:** Magacin Worker PWA
**URL:** http://localhost:5131 (or company URL)

### Login

1. Open the PWA on your device
2. Enter your email address
3. Enter your password
4. Tap "Login"

**Example Credentials:**
- Email: `gezim.maku@cungu.com`
- Password: `Worker123!`

### Home Screen

After login, you'll see:
- **Header:** Warehouse name, your name, status icons
- **AI Insights:** Predictions about upcoming work
- **My Tasks:** List of documents assigned to you

**Status Icons (top right):**
- 🟢 WiFi: Online
- 🔴 Disconnected: Offline
- 🔄 Sync: Syncing data
- ⚡ Battery: Current battery level

### Opening a Task

1. Find your task in the list
2. Each card shows:
   - Document number (e.g., "25-20AT-000336")
   - Location
   - Progress (e.g., "5/15 stavki")
   - Status badge
3. Tap "Otvori zadatak" button

### Working on Items

Once inside a task, you'll see all items you need to pick.

#### Scanning an Item

**Step 1: Start Scan**
1. Find the item in the list
2. Tap blue "Skeniraj" button
3. A modal opens

**Step 2: Enter Code**
1. Scan the barcode with your device camera
   - OR type the SKU manually
2. Tap "Nastavi"

**Step 3: Enter Quantity**
1. NumPad appears
2. Tap numbers to enter quantity
   - Example: Tap 5 for 5 pieces
3. Tap green "Potvrdi" button

**Result:**
- ✅ Item progress updates
- Progress bar fills
- Next item ready to scan

#### If You Can't Find Full Quantity

**Scenario:** You need 10 pieces but only found 7

1. Tap gray "Djelimično" button
2. NumPad opens
3. Enter actual quantity found: 7
4. Select reason from dropdown:
   - "Nema na lokaciji" (not at location)
   - "Oštećeno" (damaged)
   - "Pogrešna lokacija" (wrong location)
   - "Nedovoljno zaliha" (insufficient stock)
5. Tap "Potvrdi"

**Result:**
- ⚠️ Item marked with warning
- Shows: "Djelimično prikupljeno"
- Displays: "Nedostaje: 3"
- Reason saved for manager review

#### If You Can't Find Item At All

**Scenario:** Item is completely missing

1. Tap "Nije pronađeno" button (small, bottom)
2. Select reason (optional)
3. Tap "Potvrdi - nije pronađeno"

**Result:**
- 🔴 Item marked red
- Status: "Nije pronađeno"
- Picked quantity: 0
- Missing quantity: Full amount requested

### Completing a Document

After processing all items:

**Step 1: Review**
- Check all items are done (green ✓) or have shortages marked
- Look for orange warning: "N stavke sa manjkom"

**Step 2: Complete**
1. Scroll to bottom
2. Tap green "Završi dokument" button

**Step 3: Confirm (if shortages)**
- Modal appears: "Dokument ima N stavke sa manjkom"
- Message: "Da li želite završiti dokument sa evidentiranim manjkovima?"
- Tap "Potvrdi završetak"

**Result:**
- ✅ Document marked as complete
- You return to task list
- Shortages sent to management

### Working Offline

**What happens when offline:**
- 🔴 WiFi icon turns red
- All your actions are saved locally
- You see "Offline - akcija dodana u red" message

**What to do:**
- Continue working normally
- Scan and pick items as usual
- When online, actions sync automatically
- 🟢 WiFi turns green when connected

**Important:**
- Don't close the app until synced!
- Check sync icon (should stop spinning)

---

## For Managers

### Getting Started

**Device:** Desktop or tablet
**App:** Magacin Admin
**URL:** http://localhost:5130 (or company URL)

### Login

1. Open admin portal
2. Enter your email
3. Enter your password
4. Click "Login"

**Example Credentials:**
- Email: `admin@magacin.com`
- Password: `Admin123!`

### Navigation

**Top Menu Bar:**
- Dashboard - Overview
- Trebovanja - Documents
- Scheduler - Assign tasks
- Katalog - Article catalog
- Uvoz - Import files
- Analitika - Analytics
- Izvještaji - Reports
- **Manjkovi** ⭐ - Shortage tracking (NEW)
- AI Preporuke - Recommendations
- Korisnici - User management

### Viewing Shortage Reports

**Step 1: Navigate**
1. Click "Manjkovi" in top menu
2. Shortage Reports page opens

**Step 2: View Statistics**

Top cards show:
- **Card 1:** Total items with shortages
- **Card 2:** Total missing quantity
- **Card 3:** Total required quantity
- **Card 4:** Shortage rate (%)

**Step 3: Filter Data**

1. **By Date:**
   - Click date range picker
   - Select start date
   - Select end date
   - Data updates automatically

2. **By Status:**
   - Click status dropdown
   - Select:
     * Djelimično prikupljeno (partial)
     * Nije pronađeno (not found)
     * Oštećeno (damaged)

3. **Refresh:**
   - Click "Pretraži" button

**Step 4: Review Data**

Table shows:
- Which documents have shortages
- Which items are missing
- How much is missing
- Why (worker's reason)
- Who picked it
- When completed

**Step 5: Export to Excel**

1. Apply filters (optional)
2. Click "Preuzmi CSV" button
3. File downloads automatically
4. Open in Excel
5. Analyze or share with team

### Understanding Shortage Statuses

**🟢 None:** No shortage, fully picked
**🟠 Djelimično:** Partial quantity picked
**🔴 Nije pronađeno:** Item not located at all
**🔥 Oštećeno:** Item damaged or unusable

### Assigning Tasks (Scheduler)

1. Click "Scheduler" in menu
2. See list of unassigned documents
3. Each document shows AI suggestion
4. Options:
   - "Prihvati" - Accept AI suggestion
   - "Dodijeli ručno" - Assign manually
5. Select worker from dropdown
6. Click "Potvrdi"

**Workers to assign:**
- Only active magacioneri shown
- Shows current workload
- AI suggests optimal worker

---

## Common Tasks

### For Workers

#### Task 1: Pick a Full Order (No Shortages)

```
1. Login to PWA
2. Tap task card
3. For each item:
   a. Tap "Skeniraj"
   b. Scan barcode
   c. Enter quantity
   d. Tap "Potvrdi"
4. All items ✅ green
5. Tap "Završi dokument"
6. Done!
```

#### Task 2: Handle Partial Quantity

```
1. Open task
2. Find item with shortage
3. Tap "Djelimično"
4. Enter actual quantity found
5. Select reason: "Nedovoljno zaliha"
6. Tap "Potvrdi"
7. Item marked ⚠️ orange
8. Continue with other items
9. At end: Confirm completion with shortages
```

#### Task 3: Item Completely Missing

```
1. Open task
2. Find missing item
3. Tap "Nije pronađeno"
4. Select reason: "Nema na lokaciji"
5. Tap "Potvrdi - nije pronađeno"
6. Item marked 🔴 red
7. Continue with available items
8. Complete document (with confirmation)
```

### For Managers

#### Task 1: Weekly Shortage Analysis

```
1. Login to Admin
2. Click "Manjkovi"
3. Set date range: Last 7 days
4. Review statistics
5. Check shortage rate
6. If >5%: investigate reasons
7. Export CSV for detailed analysis
```

#### Task 2: Identify Problem Items

```
1. Open shortage reports
2. Sort table by "Nedostaje" (descending)
3. Look for items with high missing qty
4. Note SKU codes
5. Cross-reference with:
   - Catalog page
   - Inventory system
6. Take corrective action:
   - Relocate items
   - Update catalog
   - Train workers
```

#### Task 3: Monthly Export for ERP

```
1. Navigate to Manjkovi
2. Set date range: Entire month
3. Clear status filter (all types)
4. Click "Preuzmi CSV"
5. Open CSV in Excel
6. Review data quality
7. Import to ERP (Pantheon)
8. Create inventory adjustment documents
```

---

## Troubleshooting

### Worker Issues

**Problem:** "Code not found in catalog"
- **Cause:** SKU/barcode not in system
- **Solution:** Contact supervisor, use manual entry

**Problem:** "Scanned item does not match expected item"
- **Cause:** Wrong item scanned
- **Solution:** Verify item label, scan correct code

**Problem:** NumPad won't let me enter more than X
- **Cause:** Overpick protection
- **Solution:** Maximum is requested quantity, can't exceed

**Problem:** "Završi dokument" button is gray
- **Cause:** Some items not processed
- **Solution:** Mark remaining items as picked or not found

**Problem:** Actions not syncing
- **Cause:** Still offline
- **Solution:** Check WiFi icon, wait for green

### Manager Issues

**Problem:** Shortage report is empty
- **Cause:** No shortages in selected date range
- **Solution:** Expand date range or check if workers marking shortages

**Problem:** Statistics don't match table
- **Cause:** Browser cache
- **Solution:** Hard refresh (Ctrl+Shift+R)

**Problem:** CSV export has garbled characters
- **Cause:** Encoding issue
- **Solution:** Open CSV in Excel with UTF-8 encoding

**Problem:** Can't see recent shortages
- **Cause:** Worker hasn't completed document yet
- **Solution:** Shortages only appear after document completion

---

## Best Practices

### For Workers

✅ **DO:**
- Scan every item when possible
- Document shortage reasons clearly
- Complete tasks same day
- Check sync status before leaving
- Report damaged items immediately

❌ **DON'T:**
- Skip items without marking shortage
- Use vague reasons ("Other")
- Leave tasks incomplete overnight
- Force-close app while syncing
- Share your login credentials

### For Managers

✅ **DO:**
- Review shortage reports weekly
- Investigate patterns (same items, same reasons)
- Export data for monthly reconciliation
- Train workers on proper shortage marking
- Monitor shortage rate KPI

❌ **DON'T:**
- Ignore high shortage rates
- Blame workers without investigation
- Skip documentation
- Export without filters (too much data)
- Modify data in database directly

---

## Keyboard Shortcuts

### Admin (Desktop)

| Shortcut | Action |
|----------|--------|
| Alt+1 | Dashboard |
| Alt+2 | Trebovanja |
| Alt+3 | Scheduler |
| Alt+M | Manjkovi (Shortages) |
| Alt+U | Korisnici (Users) |
| Ctrl+E | Export current view |
| Ctrl+R | Refresh data |
| Ctrl+F | Focus search |

### PWA (Handheld)

**Hardware Buttons:**
- **Left Scan Button:** Trigger barcode scanner
- **Right Scan Button:** Alternative scanner
- **Power Button:** Screen on/off
- **Volume +/-:** Brightness (when screen on)

**Touch Gestures:**
- **Swipe Right:** Go back
- **Pull Down:** Refresh
- **Long Press Item:** Show item details

---

## Support & Help

### Getting Help

**Level 1: Self-Service**
- Check this user guide
- Review feature location guide
- Watch video tutorials (coming soon)

**Level 2: Supervisor**
- Ask your šef/supervisor
- Check with experienced colleagues
- Review printed quick reference cards

**Level 3: Technical Support**
- Email: support@magacin.com
- Phone: +382 XX XXX XXX
- Hours: Mon-Fri, 8 AM - 8 PM

### Reporting Bugs

Include:
1. Your name and role
2. What you were trying to do
3. What happened instead
4. Screenshot (if possible)
5. Time when it happened

**Email to:** bugs@magacin.com

---

## Updates & Training

### New Feature Announcements

- Check dashboard for notifications
- Read monthly newsletter
- Attend quarterly training sessions

### Version History

**v0.3.0 (Oct 2024)** - Shortage Tracking
- Barcode/SKU scanning
- Short-pick recording
- Shortage reports
- Offline support

**v0.2.0 (Sept 2024)** - AI Features
- AI task recommendations
- Predictive analytics
- Auto-scheduling

**v0.1.0 (May 2024)** - Initial Release
- Basic task management
- Document imports
- User management

---

## Glossary (Serbian/English)

| Serbian | English | Description |
|---------|---------|-------------|
| Trebovanje | Demand/Request | Document from store requesting items |
| Zadužnica | Assignment | Task given to specific worker |
| Stavka | Line Item | Individual item in a document |
| Magacioner | Warehouse Worker | Person who picks items |
| Šef | Supervisor | Team leader |
| Menadžer | Manager | Department manager |
| Radnja | Store/Shop | Retail location |
| Magacin | Warehouse | Storage facility |
| Artikal | Article/Product | Item in catalog |
| Šifra | SKU | Stock keeping unit code |
| Barkod | Barcode | Scannable item code |
| Manjak | Shortage | Missing quantity |
| Djelimično | Partial | Only some quantity found |
| Nije pronađeno | Not Found | Item missing completely |
| Oštećeno | Damaged | Item unusable |
| Skeniraj | Scan | Use barcode scanner |
| Potvrdi | Confirm | Accept/submit |
| Otkaži | Cancel | Abort action |
| Završi | Finish/Complete | Mark task done |

---

**Document Version:** 1.0  
**Last Updated:** 2024-10-10  
**Questions?** Contact your supervisor or support@magacin.com

