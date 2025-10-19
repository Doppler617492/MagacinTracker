#!/bin/bash
# Pantheon Integration Testing Script
# Tests authentication, API endpoints, and sync functionality

set -e  # Exit on error

echo "=========================================="
echo "🧪 PANTHEON INTEGRATION TEST SUITE"
echo "=========================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PANTHEON_BASE="http://cungu.pantheonmn.net:3003"
API_GATEWAY="http://localhost:5000"

echo "📋 Configuration:"
echo "  Pantheon API: $PANTHEON_BASE"
echo "  API Gateway:  $API_GATEWAY"
echo ""

# =========================================================================
# TEST 1: Pantheon Authentication
# =========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 1: 🔐 Pantheon Authentication"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

PANTHEON_RESPONSE=$(curl -s -X POST "$PANTHEON_BASE/login" \
  -H 'Content-Type: application/json' \
  -d '{"username":"CunguWMS","password":"C!g#2W4s5#$M6"}')

echo "Response: $PANTHEON_RESPONSE"

PANTHEON_TOKEN=$(echo "$PANTHEON_RESPONSE" | jq -r '.token // empty')

if [ -z "$PANTHEON_TOKEN" ]; then
  echo -e "${RED}❌ FAILED: No token received${NC}"
  exit 1
else
  echo -e "${GREEN}✅ SUCCESS: Token received${NC}"
  echo "Token (first 50 chars): ${PANTHEON_TOKEN:0:50}..."
fi

echo ""

# =========================================================================
# TEST 2: POST /get with getIdentWMS
# =========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 2: 📊 POST /get with getIdentWMS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

ARTICLES_RESPONSE=$(curl -s -X POST "$PANTHEON_BASE/get" \
  -H "Authorization: Bearer $PANTHEON_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"method":"getIdentWMS","offset":0,"limit":5}')

ARTICLE_COUNT=$(echo "$ARTICLES_RESPONSE" | jq '. | length')

echo "Articles fetched: $ARTICLE_COUNT"

if [ "$ARTICLE_COUNT" -gt 0 ]; then
  echo -e "${GREEN}✅ SUCCESS: Received $ARTICLE_COUNT articles${NC}"
  echo ""
  echo "Sample article:"
  echo "$ARTICLES_RESPONSE" | jq '.[0]'
else
  echo -e "${RED}❌ FAILED: No articles received${NC}"
  exit 1
fi

echo ""

# =========================================================================
# TEST 3: Database Migration Status
# =========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 3: 🗄️  Database Migration Status"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Check if new tables exist
TABLES=$(docker-compose exec -T db psql -U wmsops -d wmsops_local -t -c "
SELECT tablename FROM pg_tables 
WHERE schemaname = 'public' 
AND tablename IN ('subjects', 'doc_types', 'dispatches', 'dispatch_items', 'receipts', 'receipt_items')
ORDER BY tablename;
" 2>/dev/null | tr -d ' \n')

if [[ "$TABLES" == *"subjects"* ]] && [[ "$TABLES" == *"dispatches"* ]]; then
  echo -e "${GREEN}✅ SUCCESS: Pantheon tables exist${NC}"
  docker-compose exec -T db psql -U wmsops -d wmsops_local -c "
  SELECT tablename FROM pg_tables 
  WHERE schemaname = 'public' 
  AND tablename IN ('subjects', 'doc_types', 'dispatches', 'dispatch_items', 'receipts', 'receipt_items')
  ORDER BY tablename;
  " 2>/dev/null
else
  echo -e "${YELLOW}⚠️  WARNING: Run migration first: docker-compose exec task-service alembic upgrade head${NC}"
fi

echo ""

# =========================================================================
# TEST 4: Get Admin JWT Token
# =========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 4: 🎫 Get Admin JWT Token"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Try common admin credentials
ADMIN_LOGIN_RESPONSE=$(curl -s -X POST "$API_GATEWAY/api/auth/login" \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@cungu.com","password":"admin123"}' 2>/dev/null)

ADMIN_TOKEN=$(echo "$ADMIN_LOGIN_RESPONSE" | jq -r '.access_token // empty')

if [ -z "$ADMIN_TOKEN" ]; then
  echo -e "${YELLOW}⚠️  WARNING: Could not get admin token (may need to create admin user first)${NC}"
  echo "Response: $ADMIN_LOGIN_RESPONSE"
  echo ""
  echo "Skipping sync tests (require admin token)..."
  ADMIN_TOKEN="SKIP"
else
  echo -e "${GREEN}✅ SUCCESS: Admin token received${NC}"
  echo "Token (first 50 chars): ${ADMIN_TOKEN:0:50}..."
fi

echo ""

# =========================================================================
# TEST 5: Trigger Catalog Sync (if admin token available)
# =========================================================================
if [ "$ADMIN_TOKEN" != "SKIP" ]; then
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "TEST 5: 📚 Trigger Catalog Sync"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  
  SYNC_RESPONSE=$(curl -s -X POST "$API_GATEWAY/api/pantheon/sync/catalog?full_sync=true" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json" 2>/dev/null)
  
  echo "Response: $SYNC_RESPONSE"
  
  SYNC_STATUS=$(echo "$SYNC_RESPONSE" | jq -r '.status // empty')
  
  if [ "$SYNC_STATUS" == "success" ]; then
    echo -e "${GREEN}✅ SUCCESS: Catalog sync completed${NC}"
    echo "$SYNC_RESPONSE" | jq '.'
  else
    echo -e "${YELLOW}⚠️  Check response above for errors${NC}"
  fi
  
  echo ""
fi

# =========================================================================
# TEST 6: Verify Synced Articles in Database
# =========================================================================
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "TEST 6: 📊 Verify Synced Articles"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

docker-compose exec -T db psql -U wmsops -d wmsops_local -c "
SELECT 
  COUNT(*) as total,
  COUNT(CASE WHEN source = 'PANTHEON' THEN 1 END) as from_pantheon,
  COUNT(CASE WHEN aktivan = true THEN 1 END) as active,
  MAX(last_synced_at) as last_sync
FROM artikal;
" 2>/dev/null

echo ""

# =========================================================================
# SUMMARY
# =========================================================================
echo "=========================================="
echo "📊 TEST SUMMARY"
echo "=========================================="
echo ""
echo -e "${GREEN}✅ Pantheon Authentication: WORKING${NC}"
echo -e "${GREEN}✅ POST /get API Pattern: WORKING${NC}"
echo -e "${GREEN}✅ Article Fetch: WORKING${NC}"

if [ "$ADMIN_TOKEN" != "SKIP" ]; then
  echo -e "${GREEN}✅ Admin Token: OBTAINED${NC}"
else
  echo -e "${YELLOW}⚠️  Admin Token: SKIP (create admin user first)${NC}"
fi

echo ""
echo "🚀 NEXT STEPS:"
echo "  1. Run database migration: docker-compose exec task-service alembic upgrade head"
echo "  2. Create admin user if needed"
echo "  3. Trigger full catalog sync via Admin UI or API"
echo "  4. Monitor logs: docker-compose logs -f task-service | grep Pantheon"
echo ""
echo "📚 Documentation:"
echo "  - URGENT_PANTHEON_HOTFIX.md"
echo "  - PANTHEON_READY_FOR_TESTING.md"
echo ""

