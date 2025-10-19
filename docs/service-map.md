# Magacin Track WMS - Service Map & API Interconnections

**Document Version:** 1.0  
**Last Updated:** October 19, 2025  
**Analysis Date:** October 19, 2025

---

## Table of Contents

1. [Service Architecture](#1-service-architecture)
2. [Service Dependencies](#2-service-dependencies)
3. [API Gateway Routing](#3-api-gateway-routing)
4. [Inter-Service Communication](#4-inter-service-communication)
5. [Data Flow Diagrams](#5-data-flow-diagrams)
6. [Endpoint Matrix](#6-endpoint-matrix)
7. [Service Health Checks](#7-service-health-checks)

---

## 1. Service Architecture

### 1.1 Service Inventory

| Service | Type | Port | Language | Framework | Database | Purpose |
|---------|------|------|----------|-----------|----------|---------|
| **api-gateway** | Backend | 8123 | Python | FastAPI | - | API entry point, routing, auth |
| **task-service** | Backend | 8001 | Python | FastAPI | PostgreSQL | Core business logic, tasks, teams |
| **catalog-service** | Backend | 8002 | Python | FastAPI | PostgreSQL | Catalog management, lookup |
| **import-service** | Backend | 8003 | Python | FastAPI | PostgreSQL | File import, Pantheon sync |
| **realtime-worker** | Backend | Internal | Python | FastAPI | Redis | WebSocket bridge, Pub/Sub |
| **admin** | Frontend | 5130 | TypeScript | React | - | Admin dashboard |
| **pwa** | Frontend | 5131 | TypeScript | React+PWA | IndexedDB | Worker mobile app |
| **tv** | Frontend | 5132 | TypeScript | React | - | TV monitoring display |
| **db** | Infrastructure | 5432 | - | PostgreSQL 16 | - | Primary database |
| **redis** | Infrastructure | 6379 | - | Redis 7 | - | Cache & Pub/Sub |

**Total Services:** 10 (5 backend, 3 frontend, 2 infrastructure)

### 1.2 Service Layers

```
┌─────────────────────────────────────────────────────────┐
│                     PRESENTATION LAYER                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Admin     │  │     PWA     │  │     TV      │    │
│  │  (Browser)  │  │  (Mobile)   │  │  (Display)  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────┐
│                     API GATEWAY LAYER                    │
│  ┌───────────────────────────────────────────────────┐ │
│  │           API Gateway (Port 8123)                  │ │
│  │  • JWT Authentication                              │ │
│  │  • Request Routing                                 │ │
│  │  • Response Aggregation                            │ │
│  │  • WebSocket/SocketIO                              │ │
│  │  • CORS & Rate Limiting                            │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┼─────────────────┬──────────┐
        ▼                 ▼                 ▼          ▼
┌─────────────────────────────────────────────────────────┐
│                     SERVICE LAYER                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │  Task    │  │ Catalog  │  │ Import   │  │ Real   │ │
│  │ Service  │  │ Service  │  │ Service  │  │ time   │ │
│  │          │  │          │  │          │  │ Worker │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
        ┌─────────────────┴─────────────────┐
        ▼                                   ▼
┌─────────────────┐              ┌─────────────────┐
│   PostgreSQL    │              │      Redis      │
│   (Port 5432)   │              │   (Port 6379)   │
│  • 25+ tables   │              │  • Cache        │
│  • Migrations   │              │  • Pub/Sub      │
└─────────────────┘              └─────────────────┘
```

---

## 2. Service Dependencies

### 2.1 Dependency Graph

```
api-gateway
├── depends_on: task-service
│   └── depends_on: [db, redis]
├── depends_on: catalog-service (optional)
│   └── depends_on: [db, redis]
├── depends_on: import-service (optional)
│   └── depends_on: [db, redis, task-service]
└── depends_on: realtime-worker (optional)
    └── depends_on: [redis, api-gateway]

admin
└── depends_on: api-gateway

pwa
└── depends_on: api-gateway

tv
└── depends_on: api-gateway

task-service
├── depends_on: db
└── depends_on: redis

catalog-service
├── depends_on: db
├── depends_on: redis
└── depends_on: task-service

import-service
├── depends_on: db
├── depends_on: redis
└── depends_on: task-service

realtime-worker
├── depends_on: redis
└── depends_on: api-gateway
```

### 2.2 Startup Order

**Recommended startup sequence:**
```
1. db (PostgreSQL)
2. redis
3. task-service
4. catalog-service, import-service (parallel)
5. api-gateway
6. realtime-worker
7. admin, pwa, tv (parallel)
```

**Docker Compose handles this automatically via `depends_on`**

### 2.3 Critical Path

**Minimum services for basic operation:**
```
db → redis → task-service → api-gateway → admin/pwa
```

**Optional services:**
- `catalog-service` - Fallback to task-service catalog endpoints
- `import-service` - Can be started later for imports
- `realtime-worker` - Required only for live updates
- `tv` - Optional monitoring display

---

## 3. API Gateway Routing

### 3.1 Router Configuration

**File:** `backend/services/api_gateway/app/main.py`

| Router | Prefix | Target Service | Lines | Endpoints |
|--------|--------|----------------|-------|-----------|
| `health` | `/api` | Local | 1 | 1 |
| `auth` | `/api/auth/*` | task-service | 1 | 5+ |
| `user_management` | `/api/users/*` | task-service | 1 | 7+ |
| `catalog` | `/api/catalog/*` | task-service | 1 | 3+ |
| `trebovanja` | `/api/trebovanja/*` | task-service | 1 | 8+ |
| `zaduznice` | `/api/zaduznice/*` | task-service | 1 | 10+ |
| `worker` | `/api/worker/*` | task-service | 1 | 6+ |
| `tv` | `/api/tv/*` | task-service | 1 | 3+ |
| `kpi` | `/api/kpi/*` | task-service | 1 | 5+ |
| `ai` | `/api/ai/*` | task-service | 1 | 4+ |
| `kafka` | `/api/kafka/*` | task-service | 1 | 2+ |
| `stream` | `/api/stream/*` | task-service | 1 | 7+ |
| `teams` | `/api/teams/*` | task-service | 1 | 6+ |
| `edge` | `/api/edge/*` | task-service | 1 | 3+ |
| `reports` | `/api/reports/*` | task-service | 1 | 3+ |
| `task_analytics` | `/api/task-analytics/*` | task-service | 1 | 2+ |
| `pantheon_sync` | `/api/pantheon/*` | task-service | 1 | 5+ |
| `import_router` | `/api/import/*` | import-service | 1 | 4+ |
| `counts` | `/api/counts/*` | task-service | 1 | 3+ |
| `exceptions` | `/api/exceptions/*` | task-service | 1 | 3+ |

**Total Routers:** 20  
**Total Endpoints:** ~100+

### 3.2 Routing Strategy

**Pattern:** Backend for Frontend (BFF)

```python
# Gateway proxies requests to backend services
@router.get("/api/trebovanja")
async def list_trebovanja(request: Request):
    # 1. Extract JWT from request
    # 2. Forward to task-service:8001/trebovanja
    # 3. Return response to client
    pass
```

**Benefits:**
- Single entry point for all clients
- Centralized authentication
- Simplified CORS
- Request/response transformation
- Service discovery abstraction

---

## 4. Inter-Service Communication

### 4.1 Communication Patterns

#### HTTP REST (Synchronous)
```
api-gateway → task-service       (HTTP)
api-gateway → catalog-service    (HTTP)
api-gateway → import-service     (HTTP)
task-service → catalog-service   (HTTP, optional)
import-service → task-service    (HTTP)
```

#### Redis Pub/Sub (Asynchronous)
```
task-service → Redis → realtime-worker → WebSocket clients
                │
                └─→ All services (event broadcasting)
```

#### WebSocket (Bidirectional)
```
Browser/PWA ↔ api-gateway (SocketIO)
                │
                └─→ realtime-worker → Redis
```

### 4.2 Service-to-Service Calls

**Task Service → Catalog Service (Optional):**
```python
# File: backend/services/task_service/app/services/catalog.py
async with httpx.AsyncClient() as client:
    response = await client.get(
        f"{CATALOG_SERVICE_URL}/catalog/lookup",
        params={"code": barcode}
    )
```

**Import Service → Task Service:**
```python
# File: backend/services/import_service/app/services/processor.py
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{TASK_SERVICE_URL}/trebovanja",
        json=document_data
    )
```

**Realtime Worker → Redis:**
```python
# File: backend/services/realtime_worker/app/main.py
redis_client = redis.Redis()
pubsub = redis_client.pubsub()
pubsub.subscribe('task_updates', 'document_updates')
```

### 4.3 Event Broadcasting

**Event Types:**
- `task_created` - New task assigned
- `task_updated` - Task progress update
- `task_completed` - Task finished
- `document_created` - New document imported
- `document_completed` - Document closed
- `team_status_changed` - Team online/offline
- `worker_activity` - Worker action
- `shortage_detected` - Shortage recorded

**Pub/Sub Flow:**
```
1. Task Service updates database
   ↓
2. Publishes event to Redis
   ↓ redis.publish('task_updates', event_data)
3. Realtime Worker receives event
   ↓ pubsub.get_message()
4. Broadcasts via WebSocket
   ↓ sio.emit('task_update', data)
5. All connected clients receive update
   ↓ PWA/Admin/TV update UI
```

---

## 5. Data Flow Diagrams

### 5.1 User Login Flow

```
┌─────────┐                                     ┌─────────────┐
│ Browser │                                     │ API Gateway │
│ (Admin) │                                     │   :8123     │
└────┬────┘                                     └──────┬──────┘
     │                                                  │
     │  POST /api/auth/login                           │
     │  {username, password}                           │
     ├────────────────────────────────────────────────►│
     │                                                  │
     │                                                  │  Forward to
     │                                                  │  task-service
     │                                                  │
     │                                         ┌────────▼────────┐
     │                                         │  Task Service   │
     │                                         │     :8001       │
     │                                         └────────┬────────┘
     │                                                  │
     │                                                  │ 1. Validate
     │                                                  │    credentials
     │                                                  │ 2. Generate JWT
     │                                                  │ 3. Return token
     │                                                  │
     │◄─────────────────────────────────────────────────┤
     │  {access_token, user_info}                      │
     │                                                  │
```

### 5.2 Document Import Flow

```
┌─────────┐     ┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│  Admin  │     │ API Gateway │     │    Import    │     │     Task     │
│  Panel  │     │             │     │   Service    │     │   Service    │
└────┬────┘     └──────┬──────┘     └──────┬───────┘     └──────┬───────┘
     │                 │                    │                     │
     │ POST /api/import/upload              │                     │
     │ (multipart/form-data)                │                     │
     ├────────────────►│                    │                     │
     │                 │                    │                     │
     │                 │  Forward request   │                     │
     │                 ├───────────────────►│                     │
     │                 │                    │                     │
     │                 │                    │ 1. Save file        │
     │                 │                    │ 2. Parse CSV/Excel  │
     │                 │                    │ 3. Validate rows    │
     │                 │                    │                     │
     │                 │                    │ POST /trebovanja    │
     │                 │                    ├────────────────────►│
     │                 │                    │                     │
     │                 │                    │                     │ Save to
     │                 │                    │                     │ PostgreSQL
     │                 │                    │◄────────────────────┤
     │                 │                    │ {trebovanje_id}     │
     │                 │                    │                     │
     │                 │◄───────────────────┤                     │
     │◄────────────────┤ {import_job_id}    │                     │
     │                 │                    │                     │
```

### 5.3 Worker Picking Flow

```
┌─────┐  ┌─────────────┐  ┌──────────────┐  ┌────────────┐  ┌────────┐
│ PWA │  │ API Gateway │  │ Task Service │  │ PostgreSQL │  │ Redis  │
└──┬──┘  └──────┬──────┘  └──────┬───────┘  └─────┬──────┘  └────┬───┘
   │            │                 │                │              │
   │ POST /api/worker/tasks/{id}/pick-by-code     │              │
   │ {code, quantity}             │                │              │
   ├───────────►│                 │                │              │
   │            │                 │                │              │
   │            │  Forward        │                │              │
   │            ├────────────────►│                │              │
   │            │                 │                │              │
   │            │                 │ 1. Lookup code │              │
   │            │                 ├───────────────►│              │
   │            │                 │◄───────────────┤              │
   │            │                 │ {artikal}      │              │
   │            │                 │                │              │
   │            │                 │ 2. Update picked_qty          │
   │            │                 ├───────────────►│              │
   │            │                 │                │              │
   │            │                 │ 3. Publish event              │
   │            │                 ├──────────────────────────────►│
   │            │                 │ 'task_updated'                │
   │            │                 │                │              │
   │            │◄────────────────┤                │              │
   │◄───────────┤ {stavka_updated}│                │              │
   │            │                 │                │              │
   │ Update UI  │                 │                │   Broadcast  │
   │            │                 │                │   to all     │
   │◄───────────────────────────────────────────────────────────┤
   │ WebSocket: 'task_update'    │                │   clients    │
   │            │                 │                │              │
```

### 5.4 Team Assignment Flow

```
┌────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────┐
│ Schedu │     │ API Gateway │     │ Task Service │     │  Redis  │
│  ler   │     │             │     │              │     │         │
└───┬────┘     └──────┬──────┘     └──────┬───────┘     └────┬────┘
    │                 │                    │                   │
    │ POST /api/zaduznice                  │                   │
    │ {trebovanje_id, team_id}             │                   │
    ├────────────────►│                    │                   │
    │                 │                    │                   │
    │                 ├───────────────────►│                   │
    │                 │                    │                   │
    │                 │                    │ 1. Get team       │
    │                 │                    │    (worker1, 2)   │
    │                 │                    │                   │
    │                 │                    │ 2. Create         │
    │                 │                    │    zaduznica      │
    │                 │                    │    with team_id   │
    │                 │                    │                   │
    │                 │                    │ 3. Update         │
    │                 │                    │    trebovanje     │
    │                 │                    │    status         │
    │                 │                    │                   │
    │                 │                    │ 4. Publish event  │
    │                 │                    ├──────────────────►│
    │                 │                    │ 'task_created'    │
    │                 │                    │                   │
    │                 │◄───────────────────┤                   │
    │◄────────────────┤ {zaduznica_id}     │                   │
    │                 │                    │                   │
    │                 │                    │                   │
    │                 │  Both team members receive notification│
    │                 │◄───────────────────────────────────────┤
    │                 │  via WebSocket                         │
```

### 5.5 Pantheon Sync Flow

```
┌──────────┐     ┌─────────────┐     ┌──────────────┐     ┌─────────┐
│ Scheduler│     │ API Gateway │     │    Import    │     │Pantheon │
│  (Cron)  │     │             │     │   Service    │     │   ERP   │
└─────┬────┘     └──────┬──────┘     └──────┬───────┘     └────┬────┘
      │                 │                    │                   │
      │ POST /api/pantheon/sync/catalog     │                   │
      ├────────────────►│                    │                   │
      │                 │                    │                   │
      │                 ├───────────────────►│                   │
      │                 │                    │                   │
      │                 │                    │ GET /GetArticleWMS│
      │                 │                    ├──────────────────►│
      │                 │                    │                   │
      │                 │                    │◄──────────────────┤
      │                 │                    │ {articles[]}      │
      │                 │                    │                   │
      │                 │                    │ Upsert to DB      │
      │                 │                    │                   │
      │                 │◄───────────────────┤                   │
      │◄────────────────┤ {synced_count}     │                   │
      │                 │                    │                   │
```

---

## 6. Endpoint Matrix

### 6.1 Complete Endpoint List by Service

#### API Gateway (Entry Point: Port 8123)

**Health & Info**
```
GET    /                                  Root info
GET    /health                            Health check
GET    /metrics                           Prometheus metrics
GET    /docs                              Swagger UI
GET    /openapi.json                      OpenAPI spec
```

**Authentication** → task-service
```
POST   /api/auth/login                    User login
POST   /api/auth/device-token             Device token (TV)
POST   /api/auth/refresh                  Refresh token
GET    /api/auth/me                       Current user
POST   /api/auth/logout                   Logout
```

**User Management** → task-service
```
GET    /api/users                         List users
POST   /api/users                         Create user
GET    /api/users/{id}                    Get user
PUT    /api/users/{id}                    Update user
DELETE /api/users/{id}                    Delete user
PATCH  /api/users/{id}/password           Change password
PATCH  /api/users/{id}/activate           Activate user
```

**Catalog** → task-service
```
GET    /api/catalog/lookup                Lookup by SKU/barcode
GET    /api/catalog/articles              List articles
POST   /api/catalog/sync                  Sync catalog
```

**Trebovanja (Documents)** → task-service
```
GET    /api/trebovanja                    List documents
POST   /api/trebovanja                    Create document
GET    /api/trebovanja/{id}               Get document
PUT    /api/trebovanja/{id}               Update document
DELETE /api/trebovanja/{id}               Delete document
POST   /api/trebovanja/{id}/assign        Assign to worker
GET    /api/trebovanja/{id}/items         Get items
POST   /api/trebovanja/{id}/complete      Complete document
```

**Zaduznice (Assignments)** → task-service
```
GET    /api/zaduznice                     List assignments
POST   /api/zaduznice                     Create assignment
GET    /api/zaduznice/{id}                Get assignment
PUT    /api/zaduznice/{id}                Update assignment
DELETE /api/zaduznice/{id}                Delete assignment
POST   /api/zaduznice/{id}/start          Start task
POST   /api/zaduznice/{id}/pause          Pause task
POST   /api/zaduznice/{id}/resume         Resume task
POST   /api/zaduznice/{id}/complete       Complete task
GET    /api/zaduznice/{id}/items          Get items
```

**Worker Operations** → task-service
```
GET    /api/worker/tasks                  My tasks
GET    /api/worker/tasks/{id}             Task detail
POST   /api/worker/tasks/{stavka_id}/pick-by-code       Pick item
POST   /api/worker/tasks/{stavka_id}/short-pick         Short pick
POST   /api/worker/tasks/{stavka_id}/not-found          Not found
POST   /api/worker/documents/{id}/complete              Complete doc
```

**Teams** → task-service
```
GET    /api/teams                         List teams
POST   /api/teams                         Create team
GET    /api/teams/{id}                    Get team
PUT    /api/teams/{id}                    Update team
DELETE /api/teams/{id}                    Delete team
GET    /api/teams/{id}/performance        Team performance
GET    /api/teams/my-team                 My team info
```

**Reports** → task-service
```
GET    /api/reports/shortages             Shortage report (JSON/CSV)
GET    /api/reports/performance           Performance report
GET    /api/reports/kpi                   KPI dashboard
```

**Task Analytics** → task-service
```
GET    /api/task-analytics/summary        Analytics summary
GET    /api/task-analytics/trends         Task trends
```

**Stream Metrics** → task-service
```
GET    /api/stream/recent-events          Recent events
GET    /api/stream/worker-activity        Worker activity
GET    /api/stream/warehouse-load         Warehouse load
GET    /api/stream/throughput             Throughput metrics
GET    /api/stream/performance            Performance stats
GET    /api/stream/health                 Health status
GET    /api/stream/live                   Live metrics
```

**KPI** → task-service
```
GET    /api/kpi/dashboard                 KPI dashboard
GET    /api/kpi/worker/{id}               Worker KPIs
GET    /api/kpi/predict                   Predictive analytics
GET    /api/kpi/trends                    Trend analysis
GET    /api/kpi/efficiency                Efficiency metrics
```

**AI** → task-service
```
GET    /api/ai/recommendations            AI recommendations
POST   /api/ai/train                      Train model
GET    /api/ai/models                     List models
DELETE /api/ai/models/{id}                Delete model
```

**TV Dashboard** → task-service
```
GET    /api/tv/live                       Live dashboard
GET    /api/tv/leaderboard                Leaderboard
GET    /api/tv/queue                      Task queue
```

**Pantheon Sync** → task-service / import-service
```
POST   /api/pantheon/sync/catalog         Sync catalog
POST   /api/pantheon/sync/subjects        Sync subjects
POST   /api/pantheon/sync/receipts        Sync receipts
POST   /api/pantheon/sync/dispatches      Sync dispatches
GET    /api/pantheon/sync/status          Sync status
```

**Import** → import-service
```
POST   /api/import/upload                 Upload file
GET    /api/import/jobs                   List jobs
GET    /api/import/jobs/{id}              Job status
DELETE /api/import/jobs/{id}              Cancel job
```

**Stock Counts** → task-service
```
GET    /api/counts/stock                  Stock count data
POST   /api/counts/submit                 Submit count
GET    /api/counts/history                Count history
```

**Exceptions** → task-service
```
GET    /api/exceptions                    List exceptions
GET    /api/exceptions/{id}               Get exception
POST   /api/exceptions/{id}/resolve       Resolve exception
```

**Kafka** → task-service (mock)
```
POST   /api/kafka/publish                 Publish message
GET    /api/kafka/consume                 Consume messages
```

**Edge AI** → task-service (mock)
```
POST   /api/edge/inference                Run inference
GET    /api/edge/status                   Edge status
POST   /api/edge/sync                     Sync models
```

**Total Endpoints:** ~100+

### 6.2 WebSocket Events

**Namespace:** `/` (default)  
**Protocol:** Socket.IO over `/ws`

**Client → Server:**
```
connect                    Connect to WebSocket
disconnect                 Disconnect
tv_delta                   TV dashboard update
```

**Server → Client:**
```
task_created               New task assigned
task_updated               Task progress update
task_completed             Task finished
document_created           New document imported
document_completed         Document closed
team_status_changed        Team online/offline
worker_activity            Worker action
shortage_detected          Shortage recorded
tv_delta                   TV dashboard broadcast
```

---

## 7. Service Health Checks

### 7.1 Health Endpoints

| Service | Endpoint | Expected Response | Timeout |
|---------|----------|-------------------|---------|
| api-gateway | `GET http://localhost:8123/health` | `{"status": "ok"}` | 5s |
| task-service | `GET http://localhost:8001/health` | `{"status": "ok"}` | 5s |
| catalog-service | `GET http://localhost:8002/health` | `{"status": "ok"}` | 5s |
| import-service | `GET http://localhost:8003/health` | `{"status": "ok"}` | 5s |
| admin | `GET http://localhost:5130/` | HTML page | 5s |
| pwa | `GET http://localhost:5131/` | HTML page | 5s |
| tv | `GET http://localhost:5132/` | HTML page | 5s |
| PostgreSQL | `docker-compose exec db pg_isready` | `accepting connections` | 5s |
| Redis | `docker-compose exec redis redis-cli ping` | `PONG` | 5s |

### 7.2 Health Check Script

**File:** `scripts/health-check.sh` (create)

```bash
#!/bin/bash

echo "🏥 Magacin Track Health Check"
echo "=============================="

# API Gateway
echo -n "API Gateway: "
curl -s -f http://localhost:8123/health > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# Task Service
echo -n "Task Service: "
curl -s -f http://localhost:8001/health > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# Import Service  
echo -n "Import Service: "
curl -s -f http://localhost:8003/health > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# Admin Frontend
echo -n "Admin Panel: "
curl -s -f http://localhost:5130/ > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# PWA
echo -n "Worker PWA: "
curl -s -f http://localhost:5131/ > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# TV
echo -n "TV Display: "
curl -s -f http://localhost:5132/ > /dev/null && echo "✅ OK" || echo "❌ FAIL"

# PostgreSQL
echo -n "PostgreSQL: "
docker-compose exec -T db pg_isready > /dev/null 2>&1 && echo "✅ OK" || echo "❌ FAIL"

# Redis
echo -n "Redis: "
docker-compose exec -T redis redis-cli ping > /dev/null 2>&1 && echo "✅ OK" || echo "❌ FAIL"

echo "=============================="
echo "Health check complete!"
```

### 7.3 Monitoring Strategy

**Prometheus Metrics:**
- All backend services expose `/metrics` endpoint
- Metrics include:
  - HTTP request count/duration
  - Database query duration
  - Redis operations
  - Worker queue length
  - Active WebSocket connections

**Grafana Dashboards:**
- Service health overview
- Request rate & latency
- Database performance
- Error rates
- Worker activity

**Alerting:**
- Service down > 1 minute
- Error rate > 5%
- Response time > 2 seconds (P95)
- Database connection pool exhausted
- Redis connection failures

---

## 8. Service Communication Summary

### 8.1 Communication Matrix

| From ↓ / To → | API GW | Task | Catalog | Import | Realtime | DB | Redis |
|---------------|--------|------|---------|--------|----------|----|----|
| **admin** | HTTP | - | - | - | WS | - | - |
| **pwa** | HTTP | - | - | - | WS | - | - |
| **tv** | HTTP | - | - | - | WS | - | - |
| **api-gateway** | - | HTTP | HTTP | HTTP | - | - | - |
| **task-service** | - | - | HTTP | - | - | SQL | Cache |
| **catalog-service** | - | HTTP | - | - | - | SQL | Cache |
| **import-service** | - | HTTP | HTTP | - | - | SQL | Cache |
| **realtime-worker** | HTTP | - | - | - | - | - | Pub/Sub |

**Legend:**
- HTTP: REST API calls
- WS: WebSocket/SocketIO
- SQL: Database queries
- Cache: Redis caching
- Pub/Sub: Redis publish/subscribe

### 8.2 Latency Profile

**Typical Request Path:**
```
Client → API Gateway → Task Service → Database
  10ms      20ms          50ms         20ms    = 100ms total
```

**With Caching:**
```
Client → API Gateway → Task Service → Redis Cache
  10ms      20ms          30ms         5ms    = 65ms total
```

**WebSocket Update:**
```
Task Service → Redis → Realtime Worker → WebSocket Client
     5ms        2ms        5ms             <1ms = 12ms total
```

### 8.3 Scalability Recommendations

**Horizontal Scaling:**
1. **API Gateway:** Add multiple instances behind load balancer
2. **Task Service:** Stateless, can scale to N instances
3. **Catalog Service:** Read-heavy, good scaling candidate
4. **Import Service:** Job-based, queue-worker pattern

**Vertical Scaling:**
1. **PostgreSQL:** Increase resources first
2. **Redis:** Increase memory for larger cache

**Database Optimization:**
1. Add read replicas for reports
2. Implement connection pooling (PgBouncer)
3. Partition large tables by date
4. Add missing indexes

**Caching Strategy:**
1. Cache catalog lookups (1 hour TTL)
2. Cache user sessions (30 min TTL)
3. Cache dashboard queries (5 min TTL)
4. Implement cache warming

---

## Conclusion

The Magacin Track WMS demonstrates a **well-architected microservices system** with:

✅ Clear service boundaries  
✅ Efficient API Gateway pattern  
✅ Asynchronous event broadcasting  
✅ Comprehensive health monitoring  
✅ Scalable architecture design  
✅ Proper separation of concerns

**Next Phase:**
This service map provides the foundation for integrating Manhattan-style warehouse mapping and advanced location management features.

---

**Document Version:** 1.0  
**Maintained By:** Development Team  
**Last Updated:** October 19, 2025


