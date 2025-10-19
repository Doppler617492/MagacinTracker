# 📋 End-to-End Testing Guide - Magacin Track

**Complete Workflow Testing + Team Management Verification**

---

## 🎯 **TESTING OBJECTIVES**

Verify all functionality works correctly:
1. ✅ Excel import → Trebovanje creation
2. ✅ Task assignment → Zaduznica with team
3. ✅ Worker scanning → Real-time updates
4. ✅ Document completion → Status propagation
5. ✅ Team display → All dashboards show team info
6. ✅ Shift management → Countdown and break detection
7. ✅ Real-time sync → TV/Admin update immediately

---

## 🧪 **TEST SUITE 1: BASIC WORKFLOW**

### Test 1.1: Excel Import
**Steps:**
1. Open http://localhost:5130/import
2. Upload an Excel file with items
3. Click "Uvezi"
4. Verify success message

**Expected Results:**
- ✅ File uploads successfully
- ✅ Shows "Import completed" message
- ✅ Trebovanje created in database

**Verification:**
```bash
# Check trebovanje was created
TOKEN=$(curl -s -X POST http://localhost:8123/api/auth/device-token \
  -H "Content-Type: application/json" \
  -d '{"device_id": "tv-dashboard-001", "device_secret": "service-local"}' \
  | jq -r '.access_token')

curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/trebovanja?page=1&page_size=10" \
  | jq '.items | length'
# Should return: number of trebovanja
```

---

### Test 1.2: View in Trebovanja List
**Steps:**
1. Open http://localhost:5130/trebovanja
2. See list of imported documents
3. Click "Pregled" to view details

**Expected Results:**
- ✅ Document appears in list
- ✅ Shows dokument_broj, status, items count
- ✅ Detail view shows all items

---

### Test 1.3: Assign Task in Scheduler
**Steps:**
1. Open http://localhost:5130/scheduler
2. Select a trebovanje
3. Select a worker (Sabin or Gezim - both in Team A1)
4. Click "Dodjeli"

**Expected Results:**
- ✅ Task assigned successfully
- ✅ Zaduznica created with team_id
- ✅ Task appears in worker's list

**Verification:**
```bash
# Check zaduznica has team_id
docker-compose exec -T db psql -U wmsops -d wmsops_local -c \
  "SELECT z.id, t.name as team_name, u.first_name 
   FROM zaduznica z 
   LEFT JOIN team t ON z.team_id = t.id 
   LEFT JOIN users u ON z.magacioner_id = u.id 
   LIMIT 5;"
# Should show team name for assigned tasks
```

---

### Test 1.4: View Task in PWA
**Steps:**
1. Open http://localhost:5131
2. Login as Sabin (sabin.maku@cungu.com / test123)
3. See team banner at top
4. View assigned task

**Expected Results:**
- ✅ Team banner shows: "Team A1 | Smjena A | Partner: Gezim Maku"
- ✅ Countdown timer displays
- ✅ Task card appears in list
- ✅ Task shows items to scan

**Visual Check:**
- Purple gradient team banner
- Team name and shift badge
- Partner name with online/offline status
- Countdown in HH:MM:SS format

---

### Test 1.5: Scan Items
**Steps:**
1. In PWA, open a task
2. Enter barcode or quantity
3. Mark items as picked
4. Save

**Expected Results:**
- ✅ Items update successfully
- ✅ Progress bar updates
- ✅ Scan logged in database

**Verification:**
```bash
# Check scanlogs
docker-compose exec -T db psql -U wmsops -d wmsops_local -c \
  "SELECT COUNT(*) as scan_count FROM scanlog;"
# Should show number of scans
```

---

### Test 1.6: Complete Document
**Steps:**
1. In PWA, mark all items
2. Click "Završi Dokument"
3. Confirm completion

**Expected Results:**
- ✅ Document status changes to "done"
- ✅ Success message shown
- ✅ Task removed from active list

---

### Test 1.7: Verify Real-Time Updates
**Open simultaneously:**
- Tab 1: http://localhost:5132 (TV Dashboard)
- Tab 2: http://localhost:5130/trebovanja (Admin List)
- Tab 3: http://localhost:5131 (PWA)

**Steps:**
1. In PWA (Tab 3): Complete a document
2. **Watch TV (Tab 1):** Should update within 1-2 seconds
3. **Watch Admin (Tab 2):** Refresh to see status change

**Expected Results:**
- ✅ TV dashboard shows updated status immediately
- ✅ Admin list shows "done" status after refresh
- ✅ Realtime worker logs show event emission

**Check Logs:**
```bash
docker-compose logs --tail=5 realtime-worker
# Should show: "realtime-worker.emit" with document_complete event
```

---

## 🧪 **TEST SUITE 2: TEAM MANAGEMENT**

### Test 2.1: View Teams Page
**Steps:**
1. Open http://localhost:5130/teams
2. View teams table
3. Check shift status header

**Expected Results:**
- ✅ Shows "Aktivna Smjena: A" (if between 08:00-15:00)
- ✅ Countdown timer to next break/shift end
- ✅ Team A1 appears in table
- ✅ Shows Sabin Maku and Gezim Maku
- ✅ Shift badge shows "Smjena A" in blue
- ✅ Progress bar shows current completion

**KPI Cards Check:**
- Total tasks today
- Completed tasks
- Active teams
- Average completion percentage

---

### Test 2.2: View Team Performance
**Steps:**
1. On Teams page, click "Performanse" for Team A1
2. View detailed metrics

**Expected Results:**
- ✅ Total tasks count
- ✅ Completed tasks count
- ✅ Completion rate percentage
- ✅ Total scans
- ✅ Average speed per hour

---

### Test 2.3: Check PWA Team Banner
**Steps:**
1. Open http://localhost:5131
2. Login as any team member
3. Check banner below header

**Expected Results:**
- ✅ Purple gradient banner
- ✅ Team icon + name (Team A1)
- ✅ Shift badge (Smjena A - cyan)
- ✅ Partner name
- ✅ Partner online status (green tag)
- ✅ Countdown timer (clock icon + HH:MM:SS)
- ✅ Text: "do pauze" or "do kraja pauze"

---

### Test 2.4: Verify TV Team Display
**Steps:**
1. Open http://localhost:5132
2. Check header for shift info
3. View leaderboard section

**Expected Results:**

**Header:**
- ✅ "Aktivna Smjena: A" badge (blue background)
- ✅ Countdown timer in monospace font
- ✅ Badge changes to green for Shift B

**Leaderboard:**
- ✅ Title changes to "Timovi" (instead of "Top magacioneri")
- ✅ Team card shows:
  - Shift badge (A or B with color)
  - Team name in bold
  - Both member names below
  - Progress bar with percentage
  - "X/Y zadataka" instead of "stavki"

---

### Test 2.5: Shift Timing Test
**Test at different times:**

**At 09:30 (Shift A working):**
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/dashboard/live" \
  | jq '.shift_status.shift_a.status'
# Expected: "working"
```

**At 10:15 (Shift A break):**
- Status should be: "on_break"
- Countdown shows time until 10:30

**At 12:30 (Shift B working):**
- Active shift should be: "B"
- Both shifts can be active (overlap 12:00-15:00)

---

## 🧪 **TEST SUITE 3: STREAM METRICS**

### Test 3.1: Recent Events
```bash
TOKEN=$(curl -s -X POST http://localhost:8123/api/auth/device-token \
  -H "Content-Type: application/json" \
  -d '{"device_id": "tv-dashboard-001", "device_secret": "service-local"}' \
  | jq -r '.access_token')

curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/stream/events/recent?limit=10" \
  | jq '{total_count, events: (.events | map({type: .event_type, worker}))}'
```

**Expected:**
- Returns recent scan events
- Shows worker names
- Timestamps in ISO format

---

### Test 3.2: Worker Activity
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/stream/events/worker-activity" \
  | jq '.worker_activity'
```

**Expected:**
- Shows Sabin and Gezim
- Active tasks count
- Scans today count
- Status: active or idle

---

### Test 3.3: Warehouse Load
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/stream/events/warehouse-load" \
  | jq '.warehouse_load'
```

**Expected:**
- Shows Tranzitno Skladiste
- Total tasks, pending, in_progress, completed
- Load percentage calculated

---

### Test 3.4: All Metrics
```bash
# Stream metrics
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/stream/metrics" | jq .metrics

# Throughput
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/stream/metrics/throughput" | jq .throughput_metrics

# Performance
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/stream/metrics/performance" | jq .performance_metrics

# Health
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/stream/metrics/health" | jq .health_metrics
```

---

## 🧪 **TEST SUITE 4: ANALYTICS**

### Test 4.1: KPI Forecasting
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/kpi/predict?metric=items_completed&period=30&horizon=7" \
  | jq '{metric, horizon, confidence, trend: .summary.trend_direction, forecast_avg: .summary.forecast_avg}'
```

**Expected:**
- Returns 7-day forecast
- Shows trend direction
- Confidence score
- Actual and forecast data points

---

### Test 4.2: AI Recommendations
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  -X POST "http://localhost:8123/api/ai/recommendations" \
  | jq 'map({title, priority, confidence, impact_score})'
```

**Expected:**
- Returns 2 recommendations
- Load balancing suggestions
- Resource allocation ideas
- Confidence and impact scores

---

## 🧪 **TEST SUITE 5: TEAM FEATURES**

### Test 5.1: Teams List
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/teams" \
  | jq 'map({name, shift, members: [.worker1.first_name, .worker2.first_name]})'
```

**Expected Output:**
```json
[
  {
    "name": "Team A1",
    "shift": "A",
    "members": ["Sabin", "Gezim"]
  }
]
```

---

### Test 5.2: Live Dashboard
```bash
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/dashboard/live" \
  | jq '{
    active_shift: .shift_status.active_shift,
    active_teams,
    team: .team_progress[0] | {name: .team, members, completion, tasks: "\(.tasks_completed)/\(.tasks_total)"}
  }'
```

**Expected:**
- Active shift detected
- Team progress shown
- Completion percentage
- Member names

---

### Test 5.3: Team Performance
```bash
TEAM_ID=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/teams" | jq -r '.[0].id')

curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/teams/$TEAM_ID/performance" \
  | jq '{team_name, total_tasks, completion_rate, total_scans}'
```

**Expected:**
- Team name
- Task statistics
- Completion rate
- Scan count

---

## 🧪 **TEST SUITE 6: REAL-TIME VERIFICATION**

### Test 6.1: WebSocket Connection
**Check realtime worker:**
```bash
docker-compose logs --tail=10 realtime-worker | grep "connected\|emit"
```

**Expected:**
- Socket.IO connection confirmed
- Events being emitted to tv_delta

---

### Test 6.2: Frontend WebSocket
**Browser Console (Admin or TV):**
```javascript
// Should see:
"Admin WebSocket connected" or "Socket connected"
"Admin WebSocket received tv_delta" (when events occur)
```

---

### Test 6.3: End-to-End Real-Time Test
**Setup:**
1. Open TV dashboard: http://localhost:5132
2. Open Admin trebovanja: http://localhost:5130/trebovanja  
3. Open PWA: http://localhost:5131

**Action:**
1. In PWA: Complete a document
2. **Watch immediately:**
   - TV should update queue/status
   - Admin list should auto-refresh
   - Realtime worker should log emission

**Timing:**
- Update should appear within 1-2 seconds
- No manual refresh needed

---

## 🧪 **TEST SUITE 7: UI VERIFICATION**

### Test 7.1: Admin Teams Page
**URL:** http://localhost:5130/teams

**Checklist:**
- [ ] Page loads without errors
- [ ] Shift status header shows active shift
- [ ] Countdown timer updates every second
- [ ] KPI cards display numbers
- [ ] Teams table shows Team A1
- [ ] Both member names visible
- [ ] Progress bar renders
- [ ] Status badge shows correctly
- [ ] "Performanse" button works
- [ ] Auto-refresh every 30s

---

### Test 7.2: PWA Team Banner
**URL:** http://localhost:5131

**Checklist:**
- [ ] Banner appears below main header
- [ ] Purple gradient background
- [ ] Team icon + name (Team A1)
- [ ] Shift badge (cyan color)
- [ ] Partner name displayed
- [ ] Online status tag (green/gray)
- [ ] Countdown timer (HH:MM:SS)
- [ ] Timer updates every second
- [ ] Responsive on mobile

---

### Test 7.3: TV Team Display
**URL:** http://localhost:5132

**Checklist:**
- [ ] Shift info in header
- [ ] Active shift badge (blue for A, green for B)
- [ ] Countdown timer in monospace
- [ ] Leaderboard title: "Timovi"
- [ ] Team card shows team name
- [ ] Both member names shown
- [ ] Shift badge on card
- [ ] Progress bar animates
- [ ] Tasks count (X/Y zadataka)
- [ ] Auto-refresh every 15s

---

## 🧪 **TEST SUITE 8: DATA ACCURACY**

### Test 8.1: Team Data Consistency
**Verify team data is consistent across all interfaces:**

```bash
# Get team from API
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/teams" | jq '.[0]' > team_api.json

# Check database
docker-compose exec -T db psql -U wmsops -d wmsops_local -c \
  "SELECT id, name, shift FROM team WHERE active = true;"

# Compare: API response should match database
```

---

### Test 8.2: Shift Timing Accuracy
**Test at specific times:**

**At 08:00:** Shift A should start
**At 10:00:** Shift A break starts
**At 10:30:** Shift A break ends
**At 12:00:** Shift B starts (overlap with A)
**At 15:00:** Shift A ends
**At 14:00:** Shift B break starts
**At 14:30:** Shift B break ends
**At 19:00:** Shift B ends

**Verification:**
```bash
# Check current shift status
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/dashboard/live" \
  | jq '.shift_status | {active_shift, shift_a: .shift_a.status, shift_b: .shift_b.status}'
```

---

### Test 8.3: Task Assignment to Team
**Verify both team members see the same task:**

1. Assign task to Sabin
2. Check if team_id is set
3. Login as Gezim
4. Verify task appears in his list too

**Database Check:**
```bash
docker-compose exec -T db psql -U wmsops -d wmsops_local -c \
  "SELECT z.id, z.magacioner_id, z.team_id, t.name 
   FROM zaduznica z 
   JOIN team t ON z.team_id = t.id 
   WHERE z.team_id IS NOT NULL;"
```

---

## 🧪 **TEST SUITE 9: PERFORMANCE**

### Test 9.1: API Response Times
```bash
# Test key endpoints
for endpoint in "teams" "dashboard/live" "stream/metrics" "tv/snapshot"; do
  echo "Testing: $endpoint"
  time curl -s -H "Authorization: Bearer $TOKEN" \
    "http://localhost:8123/api/$endpoint" > /dev/null
done
```

**Expected:**
- All endpoints respond < 300ms
- No timeouts
- No 500 errors

---

### Test 9.2: Frontend Load Times
**Measure page load:**
1. Admin Teams: Should load < 2s
2. PWA with team banner: Should load < 2s
3. TV with team cards: Should load < 2s

**Browser DevTools → Network Tab:**
- Check total load time
- Verify no failed requests
- Confirm WebSocket connection

---

### Test 9.3: Auto-Refresh Verification
**Monitor network activity:**
- Admin Teams: Refreshes every 15-30s
- PWA Team Info: Refreshes every 60s
- TV Dashboard: Refreshes every 15s

**Check Console:**
- Should see periodic API calls
- WebSocket should stay connected
- No error messages

---

## ✅ **ACCEPTANCE CRITERIA**

### Functionality
- [x] All services running
- [x] Login works for all user types
- [x] Import creates trebovanja
- [x] Scheduler assigns tasks
- [x] PWA shows tasks and team info
- [x] Workers can scan and complete
- [x] TV displays real-time data
- [x] Teams page shows shift status
- [x] Stream endpoints return real data
- [x] Analytics provide insights

### Team Features
- [x] Teams stored in database
- [x] Shift logic calculates correctly
- [x] Countdown timers update
- [x] Team info shown in PWA
- [x] Team cards on TV
- [x] Admin can view team performance
- [x] Worker knows their partner

### Real-Time
- [x] WebSocket connection stable
- [x] Events published to Redis
- [x] Realtime worker forwards to Socket.IO
- [x] Frontend receives updates
- [x] Queries invalidate automatically

### UI/UX
- [x] Professional design across all dashboards
- [x] Responsive layouts
- [x] Clear visual indicators
- [x] Intuitive navigation
- [x] Proper error handling

---

## 🎯 **QUICK SMOKE TEST (5 Minutes)**

### Step 1: Check All Services (30s)
```bash
docker-compose ps
# All should be "Up"
```

### Step 2: Test Login (30s)
- Admin: http://localhost:5130
- PWA: http://localhost:5131  
- TV: http://localhost:5132
- All should load without errors

### Step 3: Check Teams (1min)
```bash
TOKEN=$(curl -s -X POST http://localhost:8123/api/auth/device-token \
  -H "Content-Type: application/json" \
  -d '{"device_id": "tv-dashboard-001", "device_secret": "service-local"}' \
  | jq -r '.access_token')

curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8123/api/teams" | jq length
# Expected: 1

curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8123/api/dashboard/live" \
  | jq '{active_shift: .shift_status.active_shift, active_teams}'
# Expected: {"active_shift": "A", "active_teams": 1}
```

### Step 4: View in Browser (2min)
- Admin Teams page: http://localhost:5130/teams
- Should show Team A1, shift A, countdown timer
- PWA: http://localhost:5131
- Should show team banner (if logged in as team member)
- TV: http://localhost:5132
- Should show "Timovi" and Team A1 card

### Step 5: Test One Workflow (1min)
- Open PWA
- View a task
- Check if team banner shows
- Verify shift countdown updates

**If all 5 steps pass → System is operational!** ✅

---

## 🐛 **TROUBLESHOOTING**

### Issue: Teams page shows no data
**Check:**
```bash
curl -s -H "Authorization: Bearer $TOKEN" "http://localhost:8123/api/teams"
```
**If empty:** Teams not created in database
**Solution:** Run team creation SQL

### Issue: Countdown not showing
**Check:**
- Current time in Belgrade (Europe/Belgrade timezone)
- If outside shift hours (before 08:00 or after 19:00), no active shift
- Countdown only shows during active shifts

### Issue: PWA team banner not appearing
**Check:**
```bash
# Login as worker and get team
curl -s -H "Authorization: Bearer <worker-token>" \
  "http://localhost:8123/api/worker/my-team"
```
**If null:** Worker not assigned to a team
**Solution:** Assign worker to team in database

### Issue: Real-time updates not working
**Check:**
1. Realtime worker running: `docker-compose ps realtime-worker`
2. WebSocket connection: Browser console for "Socket connected"
3. Redis pub/sub: `docker-compose logs realtime-worker`

---

## 📊 **SUCCESS METRICS**

### After Testing, You Should See:
- ✅ 10/10 services running
- ✅ 29 API endpoints working
- ✅ 3 frontends operational
- ✅ 1 team created and functional
- ✅ Real-time updates < 2s
- ✅ All dashboards showing team data
- ✅ Shift countdown updating every second
- ✅ 0 critical errors in logs

---

## 🎉 **TESTING COMPLETE!**

If all tests pass, the Magacin Track system with Team & Shift Management is **fully operational and production-ready**! 🚀

**Next Steps:**
1. Create more teams for Shift B
2. Assign tasks to teams
3. Monitor real-time performance
4. Use analytics for optimization

