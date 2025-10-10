# Quick Reference Card - Shortage Tracking

## 📱 Worker Quick Start (PWA)

### Login
```
URL: http://localhost:5131
User: gezim.maku@cungu.com
Pass: Worker123!
```

### Scan & Pick Flow
```
1. Tap task card
2. Tap "Skeniraj" on item
3. Scan barcode OR type SKU
4. Tap "Nastavi"
5. Enter quantity (NumPad)
6. Tap "Potvrdi"
✅ Done!
```

### Handle Shortage
```
1. Tap "Djelimično" button
2. Enter actual quantity
3. Select reason
4. Tap "Potvrdi"
⚠️ Shortage recorded
```

### Mark Not Found
```
1. Tap "Nije pronađeno"
2. Select reason (optional)
3. Tap "Potvrdi - nije pronađeno"
🔴 Item marked missing
```

### Complete Document
```
1. Process all items
2. Tap "Završi dokument"
3. If shortages: Confirm
✅ Task complete
```

---

## 🖥️ Manager Quick Start (Admin)

### Login
```
URL: http://localhost:5130
User: admin@magacin.com
Pass: Admin123!
```

### View Shortage Reports
```
1. Click "Manjkovi" in menu
2. See statistics (4 cards)
3. Filter by date/status
4. Click "Pretraži"
📊 Reports loaded
```

### Export to Excel
```
1. Apply filters (optional)
2. Click "Preuzmi CSV"
3. File downloads
4. Open in Excel
📁 Ready for analysis
```

---

## 🔧 Developer Quick Start

### API Testing
```bash
# Login
TOKEN=$(curl -s -X POST http://localhost:8123/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"gezim.maku@cungu.com","password":"Worker123!"}' \
  | jq -r '.access_token')

# Lookup code
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/catalog/lookup?code=12345"

# Pick by code
curl -X POST -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"code":"12345","quantity":5,"operation_id":"test-001"}' \
  "http://localhost:8123/api/worker/tasks/{stavka_id}/pick-by-code"

# Shortage report
curl -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/reports/shortages?format=json"
```

### Database Queries
```sql
-- Check shortages
SELECT * FROM trebovanje_stavka 
WHERE missing_qty > 0 
ORDER BY missing_qty DESC 
LIMIT 10;

-- Shortage rate by worker
SELECT 
  u.first_name || ' ' || u.last_name as worker,
  COUNT(*) filter (where ts.discrepancy_status != 'none') as shortage_count,
  COUNT(*) as total_items,
  ROUND(COUNT(*) filter (where ts.discrepancy_status != 'none')::numeric / COUNT(*) * 100, 2) as rate_pct
FROM trebovanje t
JOIN trebovanje_stavka ts ON ts.trebovanje_id = t.id
LEFT JOIN users u ON t.closed_by = u.id
WHERE t.closed_at IS NOT NULL
GROUP BY u.id, u.first_name, u.last_name
ORDER BY rate_pct DESC;
```

### Docker Commands
```bash
# Rebuild services
docker compose build task-service admin pwa

# Restart all
docker compose up -d

# View logs
docker compose logs -f task-service

# Database shell
docker compose exec db psql -U wmsops -d wmsops_local

# Run migration
docker compose exec task-service alembic upgrade head
```

---

## 📊 Key Metrics

### Worker Performance
- **Pick Rate:** Picks per hour
- **Accuracy:** (Picked / Required) × 100
- **Shortage Rate:** (Missing / Required) × 100

### Warehouse KPIs
- **Overall Shortage Rate:** < 5% target
- **Not Found Rate:** < 2% target
- **Completion Rate:** > 95% target

---

## 🚨 Emergency Contacts

**Technical Issues:**
- Supervisor: (immediate)
- IT Support: support@magacin.com
- Emergency: +382 XX XXX XXX

**Data Issues:**
- Missing items: Check with team lead
- System errors: Screenshot + email to IT

---

## ⌨️ Shortcuts

### Admin (Desktop)
- `Alt + M` → Manjkovi
- `Alt + T` → Trebovanja
- `Alt + S` → Scheduler
- `Ctrl + E` → Export
- `Ctrl + R` → Refresh

### PWA (Handheld)
- **Left Scan Button** → Trigger scanner
- **Swipe Right** → Go back
- **Pull Down** → Refresh

---

## 🎯 Decision Tree

### "What button should I click?"

**Item completely picked:**
→ Tap "Skeniraj" → Scan → Enter full quantity

**Item partially available:**
→ Tap "Djelimično" → Enter actual qty → Select reason

**Item not at location:**
→ Tap "Nije pronađeno" → Select reason

**All items processed:**
→ Tap "Završi dokument" → Confirm if shortages

**Offline:**
→ Work normally, sync happens automatically

---

## 📋 Checklists

### Before Starting Shift
- ✅ Device charged (>50%)
- ✅ Logged in to PWA
- ✅ Tasks visible
- ✅ WiFi connected (green icon)

### After Completing Task
- ✅ All items scanned or marked
- ✅ Shortages documented with reasons
- ✅ Document completed
- ✅ Sync indicator stopped spinning

### End of Shift
- ✅ All tasks completed
- ✅ Device synced (WiFi green)
- ✅ No pending actions
- ✅ Logout from PWA

---

## 💡 Pro Tips

**Workers:**
- Scan quickly, system validates automatically
- Use "Djelimično" early if you see shortage
- Check "Nedostaje" to see remaining quantity
- Reasons help improve inventory accuracy

**Managers:**
- Export weekly for trend analysis
- Compare shortage rates between workers (coaching opportunity)
- Filter by reason to identify systemic issues
- Share reports with procurement team

---

## 🔗 Related Links

- [Full Architecture →](./ARCHITECTURE.md)
- [Feature Location Guide →](./FEATURE_LOCATION_GUIDE.md)
- [User Guide →](./USER_GUIDE.md)
- [API Reference →](./API_REFERENCE.md)
- [Short-Pick Feature Docs →](./SHORT_PICK_FEATURE.md)

---

**Print this card for desk reference!**  
**Version:** 1.0  
**Updated:** 2024-10-10

