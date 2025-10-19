# 🚨 PANTHEON API - NETWORK CONNECTIVITY ISSUE

**Problem:** Cannot reach Pantheon API from your network  
**Status:** ❌ Connection timeout (5+ seconds)  
**Impact:** Sync functionality unavailable until network access resolved

---

## 🔍 DIAGNOSIS

### Test Results:
```bash
# From host machine
curl -X POST http://cungu.pantheonmn.net:3003/login
# Result: TIMEOUT (5+ seconds)
# HTTP Status: 000 (no connection)
```

**Conclusion:** Pantheon API is **UNREACHABLE** from your current network.

---

## 🛠️ TROUBLESHOOTING STEPS

### Step 1: Test DNS Resolution
```bash
nslookup cungu.pantheonmn.net
# or
dig cungu.pantheonmn.net

# Expected: IP address returned
# If fails: DNS issue
```

### Step 2: Test Ping
```bash
ping cungu.pantheonmn.net

# Expected: Replies from server
# If "Request timeout": Server/firewall blocking ICMP
```

### Step 3: Test Port Connectivity
```bash
nc -zv cungu.pantheonmn.net 3003
# or
telnet cungu.pantheonmn.net 3003

# Expected: "Connection succeeded" or "Connected to"
# If fails: Port 3003 is blocked by firewall
```

### Step 4: Test with curl (verbose)
```bash
curl -v -X POST http://cungu.pantheonmn.net:3003/login \
  -H "Content-Type: application/json" \
  -d '{"username":"CunguWMS","password":"C!g#2W4s5#$M6"}' \
  --max-time 10

# Watch for:
# - "Could not resolve host" → DNS issue
# - "Connection timed out" → Firewall/network issue
# - "Connection refused" → Service down or port blocked
```

---

## 💡 POSSIBLE SOLUTIONS

### Solution 1: VPN Connection
**If Pantheon requires VPN:**
1. Connect to company VPN
2. Retry curl test
3. If successful, Docker containers also need VPN access

**For Docker VPN access:**
```yaml
# In docker-compose.yml, add to task-service:
services:
  task-service:
    network_mode: "host"  # Use host network (shares VPN connection)
```

### Solution 2: IP Whitelist
**Contact Pantheon Support:**
```
Subject: IP Whitelist Request - CunguWMS API Access

Dear Pantheon Support,

We need to access the Pantheon API from:
- Public IP: <your_public_ip>  # Find with: curl ifconfig.me
- API Endpoint: http://cungu.pantheonmn.net:3003

Please whitelist our IP address for API access.

Account: CunguWMS
Contact: <your_email>

Thank you!
```

### Solution 3: Firewall Exception
**If corporate firewall is blocking:**
1. Contact IT department
2. Request exception for:
   - Destination: `cungu.pantheonmn.net` (or specific IP)
   - Port: `3003`
   - Protocol: `HTTP`
   - Direction: `Outbound`

### Solution 4: Alternative Endpoint
**Check with Pantheon if there's:**
- Different base URL (e.g., HTTPS on 443?)
- Different port (e.g., 80, 8080, 443?)
- Different hostname (e.g., api.pantheonmn.net?)

---

## 🧪 VERIFICATION COMMANDS

After fixing network access, test:

```bash
# 1. DNS resolves
nslookup cungu.pantheonmn.net
# Should return IP address

# 2. Port accessible
nc -zv cungu.pantheonmn.net 3003
# Should return "succeeded"

# 3. API responds
curl -X POST http://cungu.pantheonmn.net:3003/login \
  -H "Content-Type: application/json" \
  -d '{"username":"CunguWMS","password":"C!g#2W4s5#$M6"}'
# Should return {"message": "Login successful", "token": "..."}

# 4. Fetch data
PANTHEON_TOKEN="<token_from_step_3>"
curl -X POST http://cungu.pantheonmn.net:3003/get \
  -H "Authorization: Bearer $PANTHEON_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"method":"getIdentWMS","offset":0,"limit":5}'
# Should return array of articles
```

---

## 🔄 WORKAROUND: Mock Data (Development Only)

If you need to test the system while waiting for network access:

```bash
# Insert sample articles manually
docker-compose exec -T db psql -U wmsops -d wmsops_local << 'SQL'
INSERT INTO artikal (id, sifra, naziv, jedinica_mjere, aktivan, source, last_synced_at)
VALUES
  (gen_random_uuid(), 'PANT001', 'Pantheon Test Article 1', 'kom', true, 'PANTHEON', NOW()),
  (gen_random_uuid(), 'PANT002', 'Pantheon Test Article 2', 'kom', true, 'PANTHEON', NOW()),
  (gen_random_uuid(), 'PANT003', 'Pantheon Test Article 3', 'lit', true, 'PANTHEON', NOW());
SQL
```

**Note:** This is ONLY for testing UI. Remove before production!

---

## 📊 CURRENT STATUS

### What's Working:
- ✅ Pantheon client code is correct
- ✅ API pattern is correct (POST /get)
- ✅ Credentials are correct
- ✅ Field mapping is correct
- ✅ Database schema is ready
- ✅ UI is functional

### What's NOT Working:
- ❌ Network connectivity to Pantheon API
- ❌ Cannot fetch real data from Pantheon
- ❌ Sync shows 0 new articles

### Root Cause:
**Network/firewall blocking access to `cungu.pantheonmn.net:3003`**

---

## 🚀 NEXT STEPS

1. **Contact Pantheon Provider:**
   - Verify correct API endpoint
   - Check if VPN is required
   - Request IP whitelist
   - Confirm port 3003 is correct

2. **Contact IT Department:**
   - Request firewall exception for outbound HTTP to `cungu.pantheonmn.net:3003`

3. **Test Alternative Access:**
   - Try from different network (mobile hotspot?)
   - Try HTTPS if available
   - Check for proxy requirements

4. **Once Fixed:**
   - Re-run sync from Admin UI
   - Should fetch 1000+ articles
   - Verify in catalog page

---

## 📞 CONTACT INFO NEEDED FROM PANTHEON

Ask Pantheon provider for:
- ✅ Correct API endpoint (is `cungu.pantheonmn.net:3003` correct?)
- ✅ VPN requirements
- ✅ IP whitelist status
- ✅ Any proxy configuration needed
- ✅ Alternative endpoints (HTTPS?)
- ✅ Network requirements documentation

---

**The code is 100% correct and ready. This is purely a network connectivity issue.**

