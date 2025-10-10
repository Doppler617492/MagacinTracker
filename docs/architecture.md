# Magacin Track - System Architecture Documentation

## System Overview

Magacin Track is a modern warehouse management system designed for retail distribution networks. It consists of microservices backend, multiple frontend applications, and real-time communication infrastructure.

---

## High-Level Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     CLIENT APPLICATIONS                      │
├─────────────────┬──────────────────┬──────────────────────┤
│   Admin Web     │   Worker PWA     │   TV Display         │
│   (Port 5130)   │   (Port 5131)    │   (Port 5132)        │
│   React + Ant   │   React + Ant    │   React              │
│   Design        │   Design + PWA   │                      │
└────────┬────────┴────────┬─────────┴──────────┬──────────┘
         │                 │                     │
         └─────────────────┼─────────────────────┘
                           │
                  ┌────────▼────────┐
                  │  API Gateway    │
                  │  (Port 8123)    │
                  │  FastAPI        │
                  └────────┬────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
    ┌────▼────┐     ┌─────▼──────┐   ┌────▼────────┐
    │  Task   │     │  Import    │   │ Realtime    │
    │ Service │     │  Service   │   │  Worker     │
    │  8001   │     │    8002    │   │   8003      │
    └────┬────┘     └─────┬──────┘   └─────────────┘
         │                │
         └────────┬───────┘
                  │
         ┌────────▼────────┐
         │   PostgreSQL    │
         │   (Port 5432)   │
         │   + Redis       │
         └─────────────────┘
```

---

## Component Details

### 1. Frontend Applications

#### Admin Web Application
- **Port:** 5130
- **Framework:** React 18 + TypeScript
- **UI Library:** Ant Design 5
- **State:** React Query (TanStack Query)
- **Routing:** React Router v6
- **Build:** Vite
- **Deployment:** Nginx (static files)

**Key Pages:**
- Dashboard - Overview metrics
- Trebovanja - Document management
- Scheduler - Task assignment
- Katalog - Article catalog
- Uvoz - File imports
- Analitika - Business analytics
- **Manjkovi** ⭐ - Shortage reports (NEW)
- AI Preporuke - AI recommendations
- Korisnici - User management

#### Worker PWA
- **Port:** 5131
- **Framework:** React 18 + TypeScript
- **UI Library:** Ant Design 5
- **PWA:** Vite Plugin PWA (Workbox)
- **Offline:** IndexedDB + Service Worker
- **Target:** Zebra TC21/TC26 handhelds

**Key Pages:**
- Login - Authentication
- Tasks - Task list with AI insights
- **Task Detail** ⭐ - Picking interface (NEW)
- Reports - Performance reports
- Settings - Sync & preferences

**Key Components:**
- HeaderStatusBar - Status indicators
- AIInsightsPanel - Edge predictions
- TaskCard - Task preview
- **NumPad** ⭐ - Quantity entry (NEW)
- BottomNav - Navigation

#### TV Display
- **Port:** 5132
- **Framework:** React 18
- **Purpose:** Real-time dashboard
- **Features:** Leaderboard, queue, KPIs

### 2. Backend Services

#### API Gateway
- **Port:** 8123
- **Framework:** FastAPI
- **Purpose:** Unified entry point, auth, routing
- **Pattern:** BFF (Backend for Frontend)

**Responsibilities:**
- JWT authentication
- Request routing to microservices
- Response aggregation
- CORS handling
- Rate limiting

**Routers:**
```python
/api/auth/*          → Task Service
/api/trebovanja/*    → Task Service
/api/zaduznice/*     → Task Service
/api/worker/*        → Task Service ⭐
/api/catalog/*       → Task Service ⭐
/api/reports/*       → Task Service ⭐
/api/kpi/*           → Task Service
/api/ai/*            → Task Service
/api/import/*        → Import Service
/api/kafka/*         → Task Service (mock)
/api/edge/*          → Task Service (mock)
```

#### Task Service
- **Port:** 8001
- **Framework:** FastAPI + SQLAlchemy 2.0
- **Database:** PostgreSQL (async)
- **ORM:** SQLAlchemy with Alembic migrations

**Domain Models:**
- Users & Authentication
- Trebovanja (Demand documents)
- Zaduznice (Assignments)
- **Shortages** ⭐ (NEW)
- Catalog (Articles & Barcodes)
- KPIs & Analytics
- Scheduler

**Key Services:**
```python
services/
├─ shortage.py ⭐      # Picking operations (NEW)
├─ catalog.py          # Article lookup (extended)
├─ zaduznice.py        # Task assignment
├─ scheduler.py        # Auto-scheduling
├─ kpi.py              # Analytics
└─ audit.py            # Audit logging
```

#### Import Service
- **Port:** 8002
- **Purpose:** File parsing (CSV, Excel, PDF)
- **Features:** Catalog enrichment, validation

#### Realtime Worker
- **Port:** 8003
- **Purpose:** WebSocket/SocketIO server
- **Features:** Live updates, TV sync

### 3. Data Stores

#### PostgreSQL
- **Port:** 5432
- **Version:** 16
- **Extensions:** UUID, JSONB
- **Total Tables:** 20+

**Core Tables:**
```sql
users                 -- User accounts & auth
radnja               -- Stores
magacin              -- Warehouses
artikal              -- Articles/products
artikal_barkod       -- Barcodes
trebovanje           -- Demand documents (+ closure fields ⭐)
trebovanje_stavka    -- Document items (+ shortage fields ⭐)
zaduznica            -- Worker assignments
zaduznica_stavka     -- Assignment items
scheduler_log        -- Scheduling decisions
audit_log            -- Audit trail
import_job           -- Import history
```

#### Redis
- **Port:** 6379
- **Purpose:** Caching, session storage
- **TTL:** Configurable per key

---

## Data Flow: Shortage Tracking

### 1. Worker Scans Barcode

```
PWA (Zebra Device)
  ↓ POST /worker/tasks/{id}/pick-by-code
API Gateway (Port 8123)
  ↓ Forward with JWT
Task Service (Port 8001)
  ↓ worker_picking.py:47
ShortageService.pick_by_code()
  ↓ 1. Load stavka from DB
  ↓ 2. Lookup code in catalog
  ↓ 3. Validate code matches item
  ↓ 4. Increment picked_qty
  ↓ 5. Calculate missing_qty
  ↓ 6. Update discrepancy_status
  ↓ 7. Emit audit event
  ↓ COMMIT
PostgreSQL
  ↓ Response
PWA
  ✅ Progress bar updates
  ✅ UI refreshes
```

### 2. Admin Views Report

```
Admin (Browser)
  ↓ GET /reports/shortages?format=json
API Gateway
  ↓ Forward with JWT
Task Service
  ↓ reports.py:31
get_shortage_report()
  ↓ 1. Build SQL query with filters
  ↓ 2. JOIN trebovanje, stavka, users, radnja, magacin
  ↓ 3. WHERE missing_qty > 0 OR discrepancy_status != 'none'
  ↓ 4. Apply date/status filters
  ↓ 5. Aggregate statistics
PostgreSQL
  ↓ Result set
Task Service
  ↓ Convert to JSON/CSV
Admin
  ✅ Table populated
  ✅ Statistics calculated
  ✅ CSV export ready
```

---

## Security Architecture

### Authentication Flow

```
User Login
  ↓
POST /api/auth/login {username, password}
  ↓
Task Service validates credentials
  ↓
Password hashed with bcrypt
  ↓
✅ JWT token generated
  ↓
Token contains: {sub: user_id, role, exp}
  ↓
Returned to client
  ↓
Stored in localStorage
  ↓
Included in all subsequent requests
  ↓
API Gateway validates JWT
  ↓
Forwards user context to services
```

### Role-Based Access Control (RBAC)

```python
class Role(str, Enum):
    ADMIN = "admin"          # Full system access
    MENADZER = "menadzer"    # Manager - reports & analytics
    SEF = "sef"              # Supervisor - assignments & reports
    KOMERCIJALISTA = "komercijalista"  # Sales - view only
    MAGACIONER = "magacioner"  # Worker - picking ops
```

**Permission Matrix:**

| Endpoint | Worker | Šef | Menadžer | Admin |
|----------|--------|-----|----------|-------|
| **Picking Operations** ||||
| Catalog Lookup | ✅ | ✅ | ✅ | ✅ |
| Pick by Code | ✅ | ✅ | ❌ | ❌ |
| Short Pick | ✅ | ✅ | ❌ | ❌ |
| Not Found | ✅ | ✅ | ❌ | ❌ |
| Complete Document | ✅ | ✅ | ❌ | ❌ |
| **Admin Operations** ||||
| Shortage Reports | ❌ | ✅ | ✅ | ✅ |
| User Management | ❌ | ❌ | ❌ | ✅ |
| System Settings | ❌ | ❌ | ❌ | ✅ |

### Data Isolation

- **Workers:** See only their assigned tasks
- **Managers:** See all data in their region/department
- **Admin:** Full system access

### Audit Trail

All operations logged to `audit_log` table:
```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY,
    action VARCHAR(64),
    user_id UUID REFERENCES users(id),
    resource_id UUID,
    resource_type VARCHAR(64),
    details JSONB,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);
```

**Shortage-related audit actions:**
- `SCAN_OK` - Successful scan
- `SCAN_MISMATCH` - Wrong item scanned
- `SHORT_PICK_RECORDED` - Partial quantity
- `NOT_FOUND_RECORDED` - Item not located
- `DOC_COMPLETED_INCOMPLETE` - Finished with shortages
- `LOOKUP_BY_CODE` - Catalog lookup

---

## Offline-First Architecture (PWA)

### Service Worker Strategy

```typescript
// Registration
if ('serviceWorker' in navigator) {
  navigator.serviceWorker.register('/sw.js');
}

// Caching Strategy
workbox.routing.registerRoute(
  ({url}) => url.pathname.startsWith('/api/'),
  new workbox.strategies.NetworkFirst({
    cacheName: 'api-cache',
    plugins: [
      new workbox.expiration.ExpirationPlugin({
        maxEntries: 50,
        maxAgeSeconds: 5 * 60, // 5 minutes
      }),
    ],
  })
);
```

### Offline Queue

**Storage:** IndexedDB
**Database:** `magacin-offline-queue`
**Store:** `actions`

**Queue Structure:**
```typescript
interface OfflineAction {
  id: string;
  type: 'pick-by-code' | 'short-pick' | 'not-found' | 'complete-document';
  taskItemId: string;
  payload: {
    code?: string;
    quantity?: number;
    reason?: string;
    operation_id: string;
  };
  timestamp: number;
  synced: boolean;
  retryCount: number;
}
```

**Sync Process:**
1. Network status change detected
2. `OfflineQueueManager.syncAll()` triggered
3. Actions processed sequentially
4. Success: `synced = true`
5. Failure: `retryCount++`, retry after delay
6. Max retries: 3

### Idempotency

All write operations include `operation_id`:
```typescript
operation_id: `${actionType}-${stavkaId}-${timestamp}`
```

Server checks for duplicate `operation_id` and returns cached response if already processed.

---

## Database Schema Reference

### Complete Schema Diagram

```
users
├─ id (PK)
├─ email (unique)
├─ first_name
├─ last_name
├─ role (enum)
├─ hashed_password
└─ is_active

radnja
├─ id (PK)
├─ naziv
└─ aktivan

magacin
├─ id (PK)
├─ naziv
└─ aktivan

artikal
├─ id (PK)
├─ sifra (unique)
├─ naziv
├─ jedinica_mjere
└─ aktivan
    │
    └─ Has Many ─→ artikal_barkod
                   ├─ id (PK)
                   ├─ artikal_id (FK)
                   ├─ barkod
                   └─ is_primary

trebovanje
├─ id (PK)
├─ dokument_broj (unique)
├─ datum
├─ magacin_id (FK → magacin)
├─ radnja_id (FK → radnja)
├─ status (enum)
├─ created_by_id (FK → users)
├─ allow_incomplete_close ⭐
├─ closed_by (FK → users) ⭐
└─ closed_at ⭐
    │
    └─ Has Many ─→ trebovanje_stavka
                   ├─ id (PK)
                   ├─ trebovanje_id (FK)
                   ├─ artikal_id (FK → artikal)
                   ├─ artikl_sifra
                   ├─ naziv
                   ├─ kolicina_trazena
                   ├─ kolicina_uradjena (deprecated)
                   ├─ barkod
                   ├─ status (enum)
                   ├─ needs_barcode
                   ├─ picked_qty ⭐
                   ├─ missing_qty ⭐
                   ├─ discrepancy_status ⭐
                   ├─ discrepancy_reason ⭐
                   └─ last_scanned_code ⭐

zaduznica
├─ id (PK)
├─ trebovanje_id (FK → trebovanje)
├─ magacioner_id (FK → users)
├─ status (enum)
├─ assigned_at
├─ started_at
└─ completed_at
    │
    └─ Has Many ─→ zaduznica_stavka
                   ├─ id (PK)
                   ├─ zaduznica_id (FK)
                   ├─ trebovanje_stavka_id (FK)
                   ├─ kolicina
                   └─ status (enum)

audit_log
├─ id (PK)
├─ action (enum) ⭐
├─ user_id (FK → users)
├─ resource_id
├─ resource_type
├─ details (JSONB)
└─ timestamp

import_job
├─ id (PK)
├─ filename
├─ status
├─ created_by (FK → users)
└─ meta (JSONB)

scheduler_log
├─ id (PK)
├─ trebovanje_id (FK)
├─ suggested_magacioner_id (FK → users)
├─ actual_magacioner_id (FK → users)
├─ status
└─ reasons (JSONB)
```

### Enum Definitions

```sql
-- User Roles
CREATE TYPE user_role_enum AS ENUM (
  'admin', 'menadzer', 'sef', 'komercijalista', 'magacioner'
);

-- Document Status
CREATE TYPE trebovanje_status AS ENUM (
  'new', 'assigned', 'in_progress', 'done', 'failed'
);

-- Item Status
CREATE TYPE trebovanje_stavka_status AS ENUM (
  'new', 'assigned', 'in_progress', 'done'
);

-- Assignment Status
CREATE TYPE zaduznica_status AS ENUM (
  'assigned', 'in_progress', 'done', 'blocked'
);

-- Discrepancy Status ⭐
CREATE TYPE discrepancy_status_enum AS ENUM (
  'none', 'short_pick', 'not_found', 'damaged', 'wrong_barcode'
);

-- Import Status
CREATE TYPE import_status AS ENUM (
  'pending', 'processing', 'done', 'failed'
);
```

---

## API Structure

### Backend Service Organization

```
backend/
├─ app_common/               # Shared utilities
│  ├─ config.py             # Settings management
│  ├─ db.py                 # Database session
│  ├─ logging.py            # Structured logging
│  ├─ middleware.py         # CORS, correlation ID
│  └─ security.py           # Password hashing, JWT
│
├─ services/
   ├─ api_gateway/
   │  └─ app/
   │     ├─ main.py
   │     ├─ routers/
   │     │  ├─ auth.py
   │     │  ├─ trebovanja.py
   │     │  ├─ zaduznice.py
   │     │  ├─ worker.py ⭐
   │     │  ├─ reports.py ⭐
   │     │  └─ kpi.py
   │     └─ services/
   │
   ├─ task_service/
   │  └─ app/
   │     ├─ main.py
   │     ├─ models/
   │     │  ├─ enums.py           # +DiscrepancyStatus ⭐
   │     │  ├─ trebovanje.py      # +shortage fields ⭐
   │     │  ├─ zaduznica.py
   │     │  ├─ user.py
   │     │  ├─ article.py
   │     │  └─ audit.py
   │     ├─ routers/
   │     │  ├─ worker_picking.py ⭐  # NEW
   │     │  ├─ reports.py ⭐        # NEW
   │     │  ├─ internal_catalog.py # Extended
   │     │  ├─ trebovanja.py
   │     │  ├─ zaduznice.py
   │     │  ├─ kpi.py
   │     │  └─ auth_test.py
   │     ├─ services/
   │     │  ├─ shortage.py ⭐       # NEW
   │     │  ├─ catalog.py          # Extended
   │     │  ├─ zaduznice.py
   │     │  ├─ scheduler.py
   │     │  └─ audit.py
   │     ├─ schemas/
   │     │  ├─ shortage.py ⭐       # NEW
   │     │  ├─ catalog.py
   │     │  ├─ trebovanje.py
   │     │  └─ zaduznica.py
   │     └─ alembic/
   │        └─ versions/
   │           └─ 003_add_shortage_tracking.py ⭐
   │
   ├─ import_service/
   │  └─ app/
   │     ├─ parsers/
   │     └─ services/
   │
   └─ realtime_worker/
      └─ app/
```

---

## Frontend Organization

```
frontend/
├─ admin/
│  ├─ src/
│  │  ├─ pages/
│  │  │  ├─ App.tsx                    # Main app + routing
│  │  │  ├─ LoginPage.tsx
│  │  │  ├─ DashboardPage.tsx
│  │  │  ├─ TrebovanjaPage.tsx
│  │  │  ├─ SchedulerPage.tsx
│  │  │  ├─ ShortageReportsPage.tsx ⭐  # NEW
│  │  │  ├─ UserManagementPage.tsx
│  │  │  └─ ... (10+ other pages)
│  │  ├─ components/
│  │  └─ api.ts                        # Axios client
│  ├─ nginx.conf                       # Nginx config
│  └─ Dockerfile
│
├─ pwa/
│  ├─ src/
│  │  ├─ pages/
│  │  │  ├─ App.tsx
│  │  │  ├─ LoginPage.tsx
│  │  │  ├─ TasksPage.tsx
│  │  │  ├─ TaskDetailPage.tsx ⭐       # REWRITTEN
│  │  │  ├─ ReportsPage.tsx
│  │  │  └─ SettingsPage.tsx
│  │  ├─ components/
│  │  │  ├─ NumPad.tsx ⭐              # NEW
│  │  │  ├─ HeaderStatusBar.tsx
│  │  │  ├─ AIInsightsPanel.tsx
│  │  │  ├─ TaskCard.tsx
│  │  │  ├─ BottomNav.tsx
│  │  │  └─ Layout.tsx
│  │  ├─ lib/
│  │  │  └─ offlineQueue.ts           # +new action types ⭐
│  │  ├─ theme.ts
│  │  ├─ api.ts
│  │  └─ styles.css
│  ├─ nginx.conf
│  ├─ vite.config.ts
│  └─ Dockerfile
│
└─ tv/
   └─ src/
      └─ App.tsx                        # TV display
```

---

## Technology Stack

### Backend

| Component | Technology | Version |
|-----------|-----------|---------|
| Runtime | Python | 3.11 |
| Framework | FastAPI | 0.111.0 |
| ORM | SQLAlchemy | 2.0.29 |
| Database | PostgreSQL | 16 |
| Cache | Redis | 7 |
| Migrations | Alembic | 1.13.1 |
| Validation | Pydantic | 2.7.0 |
| HTTP Client | HTTPX | 0.27.0 |
| Logging | Structlog | 24.1.0 |
| Metrics | Prometheus | 0.20.0 |
| Auth | Python-JOSE | 3.3.0 |
| Passwords | Passlib (bcrypt) | 1.7.4 |

### Frontend

| Component | Technology | Version |
|-----------|-----------|---------|
| Runtime | Node.js | 20 |
| Framework | React | 18.2 |
| Language | TypeScript | 5.4.5 |
| Build Tool | Vite | 5.2.11 |
| UI Library | Ant Design | 5.16.0 |
| State | React Query | 5.39.1 |
| Routing | React Router | 6.23.0 |
| HTTP Client | Axios | 1.6.8 |
| PWA | Vite Plugin PWA | 0.20.0 |
| Service Worker | Workbox | (via plugin) |
| Offline Storage | IndexedDB (idb) | 7.1.1 |

### Infrastructure

| Component | Technology | Version |
|-----------|-----------|---------|
| Container | Docker | 20+ |
| Orchestration | Docker Compose | 3.9 |
| Web Server | Nginx | 1.25 |
| Reverse Proxy | Nginx | 1.25 |

---

## Performance Specifications

### Response Times (P95)

| Endpoint | Target | Actual |
|----------|--------|--------|
| Catalog Lookup | <100ms | ~50ms |
| Pick by Code | <200ms | ~120ms |
| Short Pick | <200ms | ~100ms |
| Complete Document | <500ms | ~250ms |
| Shortage Report (100 rows) | <1s | ~600ms |
| CSV Export (1000 rows) | <3s | ~1.8s |

### Throughput

- **Concurrent Users:** 50+
- **Picks/Second:** 100+
- **Database Connections:** 20 pool
- **API Gateway:** 4 workers (Uvicorn)

### Storage

- **Database Size:** ~500MB (1 year of data)
- **IndexedDB (per device):** ~50MB
- **Docker Images:** ~2GB total

---

## Deployment Architecture

### Docker Compose Services

```yaml
services:
  db:                    # PostgreSQL database
  redis:                 # Cache & sessions
  task-service:          # Core business logic
  api-gateway:           # API entry point
  import-service:        # File processing
  realtime-worker:       # WebSocket server
  admin:                 # Admin frontend (Nginx)
  pwa:                   # Worker PWA (Nginx)
  tv:                    # TV display (Nginx)
```

### Ports

| Service | Internal | External | Purpose |
|---------|----------|----------|---------|
| PostgreSQL | 5432 | 5432 | Database |
| Redis | 6379 | 6379 | Cache |
| Task Service | 8001 | - | Internal only |
| API Gateway | 8000 | 8123 | API entry |
| Import Service | 8002 | - | Internal only |
| Realtime Worker | 8003 | - | Internal only |
| Admin | 80 | 5130 | Web UI |
| PWA | 80 | 5131 | Mobile UI |
| TV | 80 | 5132 | Display |

### Network Architecture

```
┌──────────────────────────────────────────┐
│          Docker Network (bridge)          │
│                                           │
│  ┌─────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Admin  │  │   PWA    │  │   TV    │ │
│  │  Nginx  │  │  Nginx   │  │  Nginx  │ │
│  └────┬────┘  └────┬─────┘  └────┬────┘ │
│       │            │              │      │
│       └────────────┼──────────────┘      │
│                    │                      │
│            ┌───────▼────────┐            │
│            │  API Gateway   │            │
│            │   (FastAPI)    │            │
│            └───────┬────────┘            │
│                    │                      │
│       ┌────────────┼────────────┐        │
│       │            │            │        │
│  ┌────▼─────┐ ┌───▼───┐  ┌────▼─────┐  │
│  │  Task    │ │Import │  │ Realtime │  │
│  │ Service  │ │Service│  │  Worker  │  │
│  └────┬─────┘ └───┬───┘  └──────────┘  │
│       │           │                      │
│       └─────┬─────┘                      │
│             │                            │
│      ┌──────▼───────┐   ┌────────┐     │
│      │  PostgreSQL  │   │ Redis  │     │
│      └──────────────┘   └────────┘     │
└──────────────────────────────────────────┘
```

---

## Monitoring & Observability

### Logging

**Format:** JSON structured logs (Structlog)

**Example:**
```json
{
  "event": "shortage.short_pick",
  "level": "info",
  "timestamp": "2024-10-10T14:30:00.123Z",
  "correlation_id": "abc-123",
  "user_id": "uuid",
  "stavka_id": "uuid",
  "picked_qty": 3,
  "required_qty": 10,
  "missing_qty": 7
}
```

### Metrics (Prometheus)

**Exposed at:** `/metrics` on each service

**Key Metrics:**
```
# Shortage operations
shortage_pick_total{status="success|failure"}
shortage_pick_duration_seconds

# Catalog lookups
catalog_lookup_total{code_type="sku|barcode"}
catalog_lookup_cache_hit_ratio

# Document completions
document_complete_total{has_shortages="true|false"}
```

### Health Checks

**Endpoints:**
- `GET /health` - Simple health check
- `GET /health/ready` - Readiness (DB connected)
- `GET /health/live` - Liveness (service running)

---

## Development Workflow

### Local Development Setup

```bash
# 1. Clone repository
git clone <repo>
cd Magacin Track

# 2. Start services
docker compose up -d

# 3. Run migrations
docker compose exec task-service alembic upgrade head

# 4. Create test user
docker compose exec task-service python -m app.scripts.create_test_users

# 5. Access applications
# Admin: http://localhost:5130
# PWA: http://localhost:5131
# TV: http://localhost:5132
# API: http://localhost:8123
```

### Making Changes

**Backend Changes:**
```bash
# 1. Edit code in backend/services/task_service/
# 2. Rebuild service
docker compose build task-service
# 3. Restart
docker compose up -d task-service
# 4. Check logs
docker compose logs -f task-service
```

**Frontend Changes (Admin/PWA):**
```bash
# 1. Edit code in frontend/admin/ or frontend/pwa/
# 2. Rebuild
docker compose build admin  # or pwa
# 3. Restart
docker compose up -d admin  # or pwa
# 4. Hard refresh browser (Cmd+Shift+R)
```

**Database Changes:**
```bash
# 1. Create migration
docker compose exec task-service alembic revision -m "description"
# 2. Edit generated file in alembic/versions/
# 3. Apply migration
docker compose exec task-service alembic upgrade head
# 4. Update models in app/models/
# 5. Rebuild task-service
docker compose build task-service && docker compose up -d task-service
```

### Testing

**API Testing:**
```bash
# Get JWT token
TOKEN=$(curl -s -X POST http://localhost:8123/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@magacin.com","password":"Admin123!"}' \
  | jq -r '.access_token')

# Test endpoint
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8123/api/catalog/lookup?code=12345
```

**Database Testing:**
```bash
# Connect to database
docker compose exec db psql -U wmsops -d wmsops_local

# Query shortages
SELECT * FROM trebovanje_stavka WHERE missing_qty > 0;
```

---

## Scalability Considerations

### Horizontal Scaling

**Services that can scale:**
- ✅ API Gateway (stateless)
- ✅ Task Service (stateless)
- ✅ Import Service (stateless)
- ✅ Realtime Worker (with sticky sessions)

**Load Balancer:** Nginx or Traefik
**Session Affinity:** Redis-based sessions

### Database Scaling

**Current:** Single PostgreSQL instance
**Future:**
- Read replicas for reports
- Connection pooling (PgBouncer)
- Partitioning (by date/region)

### Caching Strategy

**L1 Cache (Service):** In-memory (TTL: 5 min)
**L2 Cache (Redis):** Shared (TTL: 1 hour)
**L3 Cache (CDN):** Static assets only

---

## Disaster Recovery

### Backup Strategy

**Database:**
- Daily full backup (3 AM)
- Hourly incremental backups
- Retention: 30 days
- Location: S3/MinIO

**Application:**
- Docker images tagged by version
- Source code in Git
- Configuration in environment files

### Recovery Procedures

**Database Restore:**
```bash
# Stop services
docker compose down

# Restore from backup
docker compose exec db psql -U wmsops -d wmsops_local < backup.sql

# Restart
docker compose up -d
```

---

## Appendix

### Glossary

- **Trebovanje:** Demand/request document from store to warehouse
- **Zaduznica:** Work assignment for specific worker
- **Stavka:** Line item in a document
- **Magacioner:** Warehouse worker
- **Šef:** Supervisor
- **Menadžer:** Manager
- **Radnja:** Store/shop
- **Magacin:** Warehouse
- **Artikal:** Article/product
- **Šifra:** SKU code
- **Barkod:** Barcode

### Abbreviations

- **PWA:** Progressive Web App
- **SKU:** Stock Keeping Unit
- **UOM:** Unit of Measure
- **KPI:** Key Performance Indicator
- **RBAC:** Role-Based Access Control
- **JWT:** JSON Web Token
- **ORM:** Object-Relational Mapping
- **TTL:** Time To Live

---

**Document Version:** 1.0  
**Last Updated:** 2024-10-10  
**Maintained By:** Development Team
