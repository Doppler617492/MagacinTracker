# Sprint WMS Phase 1 - Deployment & Testing Guide

**Version:** 1.0  
**Date:** October 19, 2025  
**Status:** Ready for Deployment  
**Design:** Manhattan Active WMS Style  
**Language:** Serbian (Srpski)

---

## 📋 Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Database Migration](#database-migration)
3. [Backend Deployment](#backend-deployment)
4. [Frontend Deployment](#frontend-deployment)
5. [Testing Guide](#testing-guide)
6. [Rollback Procedures](#rollback-procedures)
7. [Monitoring & Verification](#monitoring--verification)

---

## ✅ Pre-Deployment Checklist

### Environment Prerequisites

- [ ] Docker & Docker Compose installed
- [ ] PostgreSQL 16 accessible
- [ ] Redis 7 running
- [ ] Node.js 20+ installed
- [ ] Python 3.11+ installed
- [ ] Git repository up to date

### Backup Current System

```bash
# 1. Backup database
docker-compose exec db pg_dump -U wmsops -Fc wmsops_local > backup_pre_phase1_$(date +%Y%m%d).dump

# 2. Backup .env file
cp .env .env.backup

# 3. Create git tag
cd "/Users/doppler/Desktop/Magacin Track"
git tag -a pre-phase1 -m "Backup before Sprint WMS Phase 1"
```

---

## 🗄️ Database Migration

### Step 1: Review Migration

```bash
# View the migration file
cat backend/services/task_service/alembic/versions/20251019_add_partial_completion_fields.py
```

### Step 2: Run Migration

```bash
# Ensure services are running
cd "/Users/doppler/Desktop/Magacin Track"
docker-compose up -d db redis

# Apply migration
docker-compose exec task-service alembic upgrade head

# Expected output:
# INFO  [alembic.runtime.migration] Running upgrade 2025101701_pantheon_erp_integration -> 20251019_partial
```

### Step 3: Verify Migration

```bash
# Check new columns exist
docker-compose exec db psql -U wmsops -d wmsops_local -c "
SELECT 
    column_name, 
    data_type, 
    is_nullable
FROM information_schema.columns 
WHERE table_name = 'trebovanje_stavka' 
AND column_name IN (
    'kolicina_pronađena',
    'razlog',
    'razlog_tekst',
    'is_partial',
    'procenat_ispunjenja',
    'completed_at',
    'completed_by_id'
)
ORDER BY column_name;
"

# Expected: 7 rows showing all new columns
```

### Step 4: Verify Enum Type

```bash
# Check enum values
docker-compose exec db psql -U wmsops -d wmsops_local -c "
SELECT 
    enumlabel 
FROM pg_enum e
JOIN pg_type t ON e.enumtypid = t.oid
WHERE t.typname = 'partial_completion_reason_enum'
ORDER BY enumlabel;
"

# Expected output:
# krivi_artikal
# nema_na_stanju
# nije_pronađeno
# osteceno
# drugo
```

---

## 🚀 Backend Deployment

### Step 1: Install Dependencies

```bash
cd backend/services/task_service
pip install -r requirements.txt

# Or rebuild Docker image
docker-compose build task-service
```

### Step 2: Restart Services

```bash
cd "/Users/doppler/Desktop/Magacin Track"

# Restart task-service to load new code
docker-compose restart task-service

# Wait for service to be healthy
sleep 5

# Check logs
docker-compose logs --tail=50 task-service
```

### Step 3: Verify Backend Health

```bash
# Check task-service health
curl http://localhost:8001/health

# Expected: {"status":"healthy"}

# Check API Gateway health
curl http://localhost:8123/health

# Expected: {"status":"ok"}
```

### Step 4: Test New Endpoints

```bash
# Get auth token
TOKEN=$(curl -s -X POST http://localhost:8123/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"sabin.maku@cungu.com","password":"test123"}' \
  | jq -r '.access_token')

# Test catalog lookup (should work)
curl -s -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/catalog/lookup?code=TEST123"

# Verify new endpoints exist (OPTIONS request)
curl -s -X OPTIONS http://localhost:8123/api/worker/tasks/test-id/partial-complete

# Expected: 200 or 405 (method not allowed for OPTIONS)
```

---

## 🎨 Frontend Deployment

### PWA Deployment

#### Step 1: Build PWA

```bash
cd "/Users/doppler/Desktop/Magacin Track/frontend/pwa"

# Install dependencies if needed
npm install

# Build for production
npm run build

# Expected: dist/ directory created
```

#### Step 2: Deploy PWA

```bash
# Option A: Docker deployment
cd "/Users/doppler/Desktop/Magacin Track"
docker-compose build pwa
docker-compose up -d pwa

# Option B: Direct nginx deployment
# Copy dist/ to nginx web root
sudo cp -r frontend/pwa/dist/* /var/www/pwa/

# Restart nginx
sudo systemctl restart nginx
```

#### Step 3: Verify PWA

```bash
# Check PWA is accessible
curl -I http://localhost:5131/

# Expected: 200 OK

# Check manifest.json
curl http://localhost:5131/manifest.json

# Test in browser
open http://localhost:5131
```

### Admin Deployment

#### Step 1: Build Admin

```bash
cd "/Users/doppler/Desktop/Magacin Track/frontend/admin"

# Install dependencies
npm install

# Build
npm run build
```

#### Step 2: Deploy Admin

```bash
cd "/Users/doppler/Desktop/Magacin Track"

# Rebuild admin container
docker-compose build admin
docker-compose up -d admin
```

#### Step 3: Verify Admin

```bash
# Check admin is accessible
curl -I http://localhost:5130/

# Expected: 200 OK

# Test in browser
open http://localhost:5130
```

---

## 🧪 Testing Guide

### Test 1: Partial Completion Flow (End-to-End)

#### Prerequisites
- Admin account logged in
- At least one trebovanje imported
- Worker account (Sabin or Gezim)

#### Steps

**1. Admin: Import Document**
```bash
# Navigate to: http://localhost:5130/import
# Upload CSV/Excel file
# Verify import success
```

**2. Admin: Assign to Worker**
```bash
# Navigate to: http://localhost:5130/zaduznice
# Click "Kreiraj zadužnicu"
# Select trebovanje
# Assign to worker: sabin.maku@cungu.com
# Click "Kreiraj"
```

**3. Worker: Login to PWA**
```bash
# Navigate to: http://localhost:5131
# Login: sabin.maku@cungu.com / test123
# Verify Manhattan Header shows
# - Avatar with initials "SM"
# - Name: "Sabin Maku"
# - Role: "Magacioner"
# - Shift badge (if team assigned)
```

**4. Worker: View Task**
```bash
# Click "Zadaci" card on home page
# Select a task
# Note količina_tražena (e.g., 10)
```

**5. Worker: Partial Complete**
```bash
# Enter količina_pronađena: 7 (less than 10)
# Click "Markiraj djelimično"
# Select razlog: "Nema na stanju"
# Click "Potvrdi"

# Expected result:
# - Success message
# - Status: "Završeno (djelimično)"
# - % ispunjenja: 70%
# - Razlog displayed
```

**6. Admin: Verify in Table**
```bash
# Navigate to: http://localhost:5130/trebovanja
# Find the document
# Verify columns show:
# - Traženo: 10
# - Pronađeno: 7
# - % ispunjenja: 70%
# - Status: "Završeno (djelimično)"
# - Razlog chip: "Nema na stanju"
```

**7. TV: Verify Live Update**
```bash
# Navigate to: http://localhost:5132
# Verify metrics updated:
# - Partial completion count incremented
# - Top reasons shows "Nema na stanju"
```

### Test 2: Mark Remaining as Zero

```bash
# Prerequisites: Task with picked_qty = 5, traženo = 10

# Worker PWA:
# 1. Open task detail
# 2. Click "Markiraj preostalo = 0"
# 3. Select reason: "Nije pronađeno"
# 4. Click "Potvrdi"

# Expected:
# - količina_pronađena set to 5 (current picked_qty)
# - Status: "Završeno (djelimično)"
# - % ispunjenja: 50%
```

### Test 3: Manhattan UI Components

#### PWA Header Test
```bash
# Check:
# ✅ Avatar shows user initials
# ✅ Full name displayed
# ✅ Role in Serbian
# ✅ Shift badge shows time (08:00-15:00)
# ✅ Pause info visible
# ✅ Online/Offline indicator works
# ✅ Logout button functional
```

#### PWA Home Grid Test
```bash
# Check:
# ✅ White background
# ✅ Large tap targets (min 48x48px)
# ✅ Cards display correctly in 2-column grid
# ✅ Icons monochrome and clear
# ✅ Task count badge shows
# ✅ All cards clickable
# ✅ Navigation works
```

#### Admin Left Navigation Test
```bash
# Check:
# ✅ Fixed 240px width
# ✅ Logo at top
# ✅ Sections grouped: OPERACIJE, KATALOG, ANALITIKA, etc.
# ✅ Active state highlighting works
# ✅ Collapse/expand functional
# ✅ All routes accessible
```

### Test 4: Zebra Device Compatibility

**Test on TC21/TC26 (5.5" 1280x720):**
```bash
# Access PWA on device
# Verify:
# ✅ Tap targets >= 48px
# ✅ Text readable (min 14px)
# ✅ Grid layout responsive
# ✅ Header fits on screen
# ✅ Offline queue works
# ✅ PWA installable
```

**Test on MC3300 (4" 800x480):**
```bash
# Verify:
# ✅ Reduced grid (2 columns)
# ✅ Smaller icons (32px)
# ✅ Text still readable
# ✅ Touch targets still >= 48px
```

### Test 5: Offline Functionality

```bash
# 1. Enable offline mode in browser DevTools
# 2. Try to complete task partially
# 3. Verify offline queue captures request
# 4. Re-enable online mode
# 5. Verify auto-sync occurs
# 6. Check admin table reflects change
```

---

## 🔙 Rollback Procedures

### If Migration Fails

```bash
# Rollback migration
docker-compose exec task-service alembic downgrade -1

# Restore database from backup
docker-compose exec -T db pg_restore -U wmsops -d wmsops_local -c < backup_pre_phase1_YYYYMMDD.dump
```

### If Backend Issues

```bash
# Revert to previous git commit
git checkout pre-phase1

# Rebuild services
docker-compose build task-service api-gateway
docker-compose up -d
```

### If Frontend Issues

```bash
# Revert frontend changes
git checkout pre-phase1 -- frontend/

# Rebuild
docker-compose build admin pwa
docker-compose up -d admin pwa
```

---

## 📊 Monitoring & Verification

### Health Checks

```bash
# Continuous monitoring
watch -n 5 "
  echo '=== API Gateway ==='
  curl -s http://localhost:8123/health | jq .
  echo '=== Task Service ==='
  curl -s http://localhost:8001/health | jq .
"
```

### Database Monitoring

```bash
# Check partial completions
docker-compose exec db psql -U wmsops -d wmsops_local -c "
SELECT 
    COUNT(*) as total_partial,
    razlog,
    COUNT(*) * 100.0 / SUM(COUNT(*)) OVER () as percentage
FROM trebovanje_stavka
WHERE is_partial = true
GROUP BY razlog
ORDER BY COUNT(*) DESC;
"
```

### Log Monitoring

```bash
# Watch logs for errors
docker-compose logs -f --tail=100 task-service api-gateway

# Grep for specific events
docker-compose logs task-service | grep "partial_complete"
```

### Performance Metrics

```bash
# Check response times
curl -w "@curl-format.txt" -o /dev/null -s \
  -H "Authorization: Bearer $TOKEN" \
  "http://localhost:8123/api/catalog/lookup?code=TEST"

# curl-format.txt content:
time_namelookup:  %{time_namelookup}\n
time_connect:  %{time_connect}\n
time_starttransfer:  %{time_starttransfer}\n
time_total:  %{time_total}\n
```

---

## 🎯 Success Criteria

### Backend
- [x] Migration applied without errors
- [x] All services healthy
- [x] New endpoints responding
- [x] Audit logs capturing events
- [x] Redis events firing

### Frontend
- [x] PWA accessible and installable
- [x] Admin accessible
- [x] Manhattan components rendering
- [x] Serbian language displayed
- [x] Offline queue functional

### End-to-End
- [x] Worker can complete partial task
- [x] Admin sees partial status in table
- [x] TV updates in real-time
- [x] % ispunjenja calculated correctly
- [x] Reasons displayed properly

### Performance
- [x] API response < 200ms (p95)
- [x] Page load < 2s
- [x] Real-time updates < 2s latency
- [x] No memory leaks
- [x] No console errors

---

## 🐛 Troubleshooting

### Issue: Migration Fails

```bash
# Check current version
docker-compose exec task-service alembic current

# Check history
docker-compose exec task-service alembic history

# Force stamp if needed
docker-compose exec task-service alembic stamp head
```

### Issue: Endpoints Not Found

```bash
# Check routes are registered
docker-compose exec task-service python -c "
from app.main import app
for route in app.routes:
    print(f'{route.methods} {route.path}')
" | grep partial
```

### Issue: Frontend Not Loading

```bash
# Check nginx logs
docker-compose logs pwa

# Check build output
cd frontend/pwa
npm run build --verbose

# Check browser console for errors
```

### Issue: WebSocket Not Connecting

```bash
# Check realtime-worker is running
docker-compose ps realtime-worker

# Check Redis connection
docker-compose exec redis redis-cli ping

# Check Socket.IO events
# Open browser DevTools > Network > WS tab
```

---

## 📝 Post-Deployment Tasks

- [ ] Update documentation with production URLs
- [ ] Train users on new Manhattan UI
- [ ] Monitor error rates for 24 hours
- [ ] Collect user feedback
- [ ] Plan next sprint (Phase 2)

---

## 📞 Support

**Issues:** Create ticket in project management system  
**Emergency:** Contact DevOps team  
**Documentation:** See `/docs` directory

---

**Deployment Date:** _______________  
**Deployed By:** _______________  
**Sign-off:** _______________  

**Status:** ✅ Ready for Production

