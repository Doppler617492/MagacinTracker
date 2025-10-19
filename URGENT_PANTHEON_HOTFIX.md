# 🚨 URGENT PANTHEON CREDENTIALS HOTFIX

**Date:** October 17, 2025  
**Severity:** CRITICAL - Wrong credentials hardcoded  
**Status:** ✅ Code fixed, awaiting rebuild & test

---

## ❌ PROBLEM

1. **Wrong Base URL:** `http://109.72.96.136:3003` → Should be `http://cungu.pantheonmn.net:3003`
2. **Wrong Username:** `CunguDeklaracije` → Should be `CunguWMS`
3. **Wrong Password:** `0778657825` → Should be `C!g#2W4s5#$M6`
4. **Wrong API Pattern:** Used GET `/getIdentWMS` → Should be POST `/get` with `{"method": "getIdentWMS"}`
5. **Wrong Response Format:** Expected `{"api_token": "..."}` → Should be `{"status": 0, "token": "..."}`

---

## ✅ FIXES APPLIED

### File 1: `backend/app_common/pantheon_config.py`
**Changed:**
```python
# OLD (WRONG)
base_url: str = Field(default="http://109.72.96.136:3003")
username: str = Field(default="CunguDeklaracije")
password: str = Field(default="0778657825")

# NEW (CORRECT)
base_url: str = Field(default="http://cungu.pantheonmn.net:3003")
username: str = Field(default="CunguWMS")
password: str = Field(default="C!g#2W4s5#$M6")
```

### File 2: `backend/app_common/pantheon_client.py`
**Changed:**

1. **Authentication Response Format:**
```python
# OLD
data.get("api_token")

# NEW
if data.get("status") == 0:
    self._token = data.get("token")
```

2. **All Data Methods (getIdentWMS, GetSubjectWMS, GetIssueDocWMS, GetReceiptDocWMS):**
```python
# OLD (WRONG)
return await self._request_with_retry("GET", "/getIdentWMS", params=params)

# NEW (CORRECT)
body = {
    "method": "getIdentWMS",
    "offset": offset,
    "limit": limit,
    "filters": {
        "adTimeChg": {
            "operator": ">=",
            "value": "2025-10-01T00:00:00"
        }
    }
}
return await self._request_with_retry("POST", "/get", json=body)
```

**All 4 methods now use:**
- ✅ `POST /get` endpoint
- ✅ `{"method": "..."}` in body
- ✅ `filters` with operator/value structure
- ✅ Correct filter fields:
  - `getIdentWMS`: `adTimeChg` with `>=`
  - `GetSubjectWMS`: `c.adTimeChg` with `>`
  - `GetIssueDocWMS`: `m.adDate` with `>`
  - `GetReceiptDocWMS`: `m.adDate` with `>`

---

## 🔥 IMMEDIATE ACTIONS REQUIRED

### Step 1: Purge Bad Tokens (if Redis is used)
```bash
# If you have Redis caching tokens
docker-compose exec redis redis-cli KEYS 'pantheon:token:*' | xargs docker-compose exec redis redis-cli DEL
```

### Step 2: Rebuild Services
```bash
cd /Users/doppler/Desktop/Magacin\ Track

# Rebuild affected services
docker-compose build task-service api-gateway catalog-service import-service

# Restart with fresh code
docker-compose up -d task-service api-gateway catalog-service import-service
```

### Step 3: Verify Services Started
```bash
sleep 5
docker-compose logs --tail=50 task-service api-gateway | grep -E "(Started|ERROR|Authenticating)"
```

### Step 4: Manual Test - Authentication
```bash
# Test new credentials directly
curl -X POST http://cungu.pantheonmn.net:3003/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "CunguWMS",
    "password": "C!g#2W4s5#$M6"
  }'
```

**Expected Response:**
```json
{
  "status": 0,
  "token": "eyJhbGci..."
}
```

**Save token:**
```bash
PANTHEON_TOKEN="<paste_token_here>"
```

### Step 5: Manual Test - POST /get with method
```bash
# Test getIdentWMS with new pattern
curl -X POST http://cungu.pantheonmn.net:3003/get \
  -H "Authorization: Bearer $PANTHEON_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "getIdentWMS",
    "offset": 0,
    "limit": 5
  }'
```

**Expected:** JSON response with articles array

### Step 6: Get Admin Token
```bash
ADMIN_TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@cungu.com", "password": "admin123"}' | jq -r '.access_token')

echo "Admin token: $ADMIN_TOKEN"
```

### Step 7: Trigger Catalog Sync
```bash
curl -X POST "http://localhost:5000/api/pantheon/sync/catalog?full_sync=true" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.'
```

**Watch logs:**
```bash
docker-compose logs -f task-service | grep -E "(Authenticating|Authentication|Pantheon|catalog)"
```

**Expected:**
- ✅ "🔐 Authenticating with Pantheon API: CunguWMS @ http://cungu.pantheonmn.net:3003"
- ✅ "✅ Authentication successful"
- ✅ "✅ Catalog sync completed in X.XXs: N fetched, M created"

### Step 8: Verify Synced Data
```bash
docker-compose exec db psql -U wmsops -d wmsops_local -c "
SELECT 
  COUNT(*) as total,
  COUNT(CASE WHEN source = 'PANTHEON' THEN 1 END) as from_pantheon,
  MAX(last_synced_at) as last_sync
FROM artikal;
"
```

### Step 9: Test Other Syncs
```bash
# Subjects
curl -X POST "http://localhost:5000/api/pantheon/sync/subjects" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.'

# Dispatches (last 7 days)
DATE_FROM=$(date -v-7d +%Y-%m-%d)
curl -X POST "http://localhost:5000/api/pantheon/sync/dispatches?date_from=$DATE_FROM" \
  -H "Authorization: Bearer $ADMIN_TOKEN" | jq '.'
```

---

## 🔐 SECURITY ACTIONS (AFTER VALIDATION)

### ⚠️ CRITICAL: Password Rotation

**The password `C!g#2W4s5#$M6` was exposed in this document and code!**

1. **Contact Pantheon provider immediately** to rotate credentials
2. **Get new password** from provider
3. **Update config:**
```python
# backend/app_common/pantheon_config.py
password: str = Field(default="<NEW_PASSWORD_FROM_PROVIDER>")
```
4. **Rebuild & restart** services
5. **Never commit passwords** to Git again

### Git History Scrubbing (if passwords were committed)

```bash
# Check if passwords are in git history
git log --all --full-history -S "0778657825" -- .
git log --all --full-history -S "C!g#2W4s5#$M6" -- .

# If found, use BFG Repo-Cleaner or git filter-repo
# WARNING: This rewrites history, coordinate with team!

# Example with git filter-repo (install first)
git filter-repo --replace-text <(echo '0778657825==>REDACTED')
git filter-repo --replace-text <(echo 'C!g#2W4s5#$M6==>REDACTED')

# Force push (DANGEROUS - backup first!)
git push --force --all
```

### Store Secrets Properly

**DO NOT hardcode passwords!** Use:
- Kubernetes Secrets
- Docker Secrets
- Vault (HashiCorp)
- 1Password
- AWS Secrets Manager

**Update code to read from env:**
```python
# backend/app_common/pantheon_config.py
password: str = Field(env="PANTHEON_PASSWORD")  # Read from env only
```

---

## 📊 Validation Checklist

- [ ] Services rebuilt with correct credentials
- [ ] Authentication succeeds with status=0, token=...
- [ ] POST /get with method works
- [ ] Catalog sync completes successfully
- [ ] Articles appear in database with source='PANTHEON'
- [ ] Subjects sync works
- [ ] Dispatches sync works with exists_in_wms logic
- [ ] Admin UI shows synced data
- [ ] No authentication errors in logs
- [ ] Rate limiting (1 RPS) is respected
- [ ] Circuit breaker works on failures
- [ ] Password rotated with provider
- [ ] Git history scrubbed (if needed)
- [ ] Secrets moved to vault (not hardcoded)

---

## 🚨 IF VALIDATION FAILS

**Check logs:**
```bash
# Task service logs
docker-compose logs --tail=100 task-service | grep -E "(ERROR|Exception|401|403|Authentication)"

# API gateway logs
docker-compose logs --tail=100 api-gateway | grep -E "(ERROR|Exception|401|403)"
```

**Common Issues:**
1. **401 Unauthorized** → Credentials still wrong, check pantheon_config.py
2. **404 Not Found** → Endpoint wrong, should be POST /get
3. **400 Bad Request** → Body format wrong, check method/filters structure
4. **Circuit breaker OPEN** → Too many failures, restart services
5. **Empty response** → No data in Pantheon for date range, adjust filters

**Contact support if stuck!**

---

**Status:** ✅ Code fixed, awaiting validation
**Next:** Run Step 1-9 above, then rotate password

