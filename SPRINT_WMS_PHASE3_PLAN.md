# Sprint WMS Phase 3 - Location-Based WMS Implementation Plan
## Directed Put-Away + Directed Picking + Cycle Counting + Map View

**Start Date:** October 19, 2025  
**Target Completion:** 14-16 days  
**Design Reference:** Manhattan Associates Active WMS  
**Language:** Serbian (Srpski)  
**Complexity:** HIGH - Enterprise-grade WMS features

---

## 🎯 Executive Summary

Transform Magacin Track into a **full-featured location-based WMS** with:

✅ **Location Hierarchy** - Zona → Regal → Polica → Bin  
✅ **Directed Put-Away** - AI-suggested optimal storage locations  
✅ **Directed Picking** - Route optimization (shortest path)  
✅ **Cycle Counting** - Inventory accuracy verification  
✅ **Map View** - 2D warehouse visualization  
✅ **Enhanced Team/Shift** - Shift-based task assignment  
✅ **Advanced KPI** - Putaway time, picking time, occupancy, accuracy  

**Pattern:** Manhattan Active WMS - enterprise location management  
**Integration:** Seamless with Phase 1 & 2 (no breaking changes)

---

## 📊 Phase 3 Scope (250 Implementation Points)

### Database Schema (Days 1-2)

#### Location Hierarchy

```sql
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    naziv VARCHAR(128) NOT NULL,
    code VARCHAR(32) UNIQUE NOT NULL,  -- e.g., "ZA-R03-P02-B07"
    tip location_type_enum NOT NULL,    -- zone, regal, polica, bin
    parent_id UUID REFERENCES locations(id),
    magacin_id UUID REFERENCES magacin(id),
    zona VARCHAR(32),                   -- Denormalized for quick lookup
    x_coordinate NUMERIC(8,2),          -- For map view
    y_coordinate NUMERIC(8,2),
    capacity_max NUMERIC(12,3),         -- Max cubic meters or weight
    capacity_current NUMERIC(12,3) DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TYPE location_type_enum AS ENUM (
    'zone',    -- Zona
    'regal',   -- Regal
    'polica',  -- Polica
    'bin'      -- Bin
);

-- Indexes for performance
CREATE INDEX idx_locations_parent ON locations(parent_id);
CREATE INDEX idx_locations_magacin ON locations(magacin_id);
CREATE INDEX idx_locations_zona ON locations(zona);
CREATE INDEX idx_locations_tip ON locations(tip);
CREATE INDEX idx_locations_code ON locations(code);

-- Example hierarchy:
-- ZONA-A (zone)
--   └── REGAL-A1 (regal)
--       └── POLICA-A1-1 (polica)
--           ├── BIN-A1-1-01 (bin)
--           ├── BIN-A1-1-02 (bin)
--           └── BIN-A1-1-03 (bin)
```

#### Article-Location Mapping

```sql
CREATE TABLE article_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artikal_id UUID REFERENCES artikal(id) NOT NULL,
    location_id UUID REFERENCES locations(id) NOT NULL,
    quantity NUMERIC(12,3) NOT NULL DEFAULT 0,
    uom VARCHAR(32) NOT NULL DEFAULT 'PCS',
    last_counted_at TIMESTAMP,
    last_moved_at TIMESTAMP,
    is_primary_location BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    CONSTRAINT unique_article_location UNIQUE (artikal_id, location_id)
);

CREATE INDEX idx_article_locations_artikal ON article_locations(artikal_id);
CREATE INDEX idx_article_locations_location ON article_locations(location_id);
CREATE INDEX idx_article_locations_primary ON article_locations(is_primary_location);
```

#### Cycle Counting

```sql
CREATE TABLE cycle_counts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    location_id UUID REFERENCES locations(id),
    scheduled_at TIMESTAMP NOT NULL,
    assigned_to_id UUID REFERENCES users(id),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status cycle_count_status_enum DEFAULT 'scheduled',
    count_type VARCHAR(32),  -- 'zone', 'regal', 'article', 'random'
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE cycle_count_items (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    cycle_count_id UUID REFERENCES cycle_counts(id) ON DELETE CASCADE,
    artikal_id UUID REFERENCES artikal(id),
    location_id UUID REFERENCES locations(id),
    system_quantity NUMERIC(12,3) NOT NULL,
    counted_quantity NUMERIC(12,3),
    variance NUMERIC(12,3),
    variance_percent NUMERIC(5,2),
    reason VARCHAR(255),
    counted_by_id UUID REFERENCES users(id),
    counted_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TYPE cycle_count_status_enum AS ENUM (
    'scheduled',   -- Zakazano
    'in_progress', -- U toku
    'completed',   -- Završeno
    'cancelled'    -- Otkazano
);
```

#### Putaway & Picking

```sql
-- Add location tracking to existing tables
ALTER TABLE receiving_item
ADD COLUMN suggested_location_id UUID REFERENCES locations(id),
ADD COLUMN actual_location_id UUID REFERENCES locations(id),
ADD COLUMN putaway_at TIMESTAMP,
ADD COLUMN putaway_by_id UUID REFERENCES users(id);

ALTER TABLE zaduznica_stavka
ADD COLUMN pick_location_id UUID REFERENCES locations(id),
ADD COLUMN pick_sequence INTEGER,
ADD COLUMN picked_at TIMESTAMP;

-- Putaway/Pick tracking
CREATE TABLE putaway_tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    receiving_item_id UUID REFERENCES receiving_item(id),
    suggested_location_id UUID REFERENCES locations(id),
    actual_location_id UUID REFERENCES locations(id),
    quantity NUMERIC(12,3) NOT NULL,
    status VARCHAR(32) DEFAULT 'pending',
    assigned_to_id UUID REFERENCES users(id),
    completed_at TIMESTAMP,
    duration_seconds INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE pick_routes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    zaduznica_id UUID REFERENCES zaduznica(id),
    route_data JSONB,  -- [{location_id, artikal_id, sequence, qty}]
    total_distance_meters NUMERIC(8,2),
    estimated_time_minutes INTEGER,
    actual_time_minutes INTEGER,
    created_at TIMESTAMP DEFAULT NOW()
);
```

---

### Backend Services (Days 3-5)

#### LocationService

```python
class LocationService:
    """Manage warehouse location hierarchy"""
    
    async def get_location_tree(self, magacin_id: UUID) -> dict:
        """Get full hierarchy as nested tree"""
        pass
    
    async def create_location(self, data: CreateLocationRequest) -> Location:
        """Create zone/regal/polica/bin"""
        pass
    
    async def get_bin_occupancy(self, location_id: UUID) -> dict:
        """Calculate occupancy percentage"""
        pass
    
    async def find_available_bins(
        self, 
        zona: Optional[str] = None,
        min_capacity: Optional[float] = None
    ) -> List[Location]:
        """Find available bins matching criteria"""
        pass
```

#### DirectedPutAwayService

```python
class DirectedPutAwayService:
    """AI-powered put-away location suggestions"""
    
    async def suggest_location(
        self,
        artikal_id: UUID,
        quantity: float,
        magacin_id: UUID
    ) -> LocationSuggestion:
        """
        Suggest optimal storage location
        
        Algorithm:
        1. Get article class/category
        2. Find suitable zones for class
        3. Calculate available bins
        4. Score by:
           - Distance from receiving area (weight: 0.3)
           - Same-class grouping (weight: 0.3)
           - Capacity match (weight: 0.2)
           - Occupancy balance (weight: 0.2)
        5. Return top 3 suggestions
        """
        pass
    
    async def execute_putaway(
        self,
        receiving_item_id: UUID,
        location_id: UUID,
        user_id: UUID
    ) -> PutawayResult:
        """
        Execute put-away to location
        1. Validate location capacity
        2. Update article_locations
        3. Update location occupancy
        4. Record putaway_tasks
        5. Audit log
        """
        pass
```

#### DirectedPickingService

```python
class DirectedPickingService:
    """Route optimization for picking"""
    
    async def generate_pick_route(
        self,
        zaduznica_id: UUID
    ) -> PickRoute:
        """
        Generate optimized picking route
        
        Algorithm:
        1. Get all items in zaduznica
        2. Find primary location for each article
        3. Sort by zone → regal → polica → bin (proximity)
        4. Calculate total distance
        5. Estimate time (items/hour * distance)
        6. Return route with sequence
        """
        pass
    
    async def get_next_pick(
        self,
        zaduznica_id: UUID,
        current_location: Optional[UUID] = None
    ) -> NextPickLocation:
        """Get next location in route"""
        pass
```

#### CycleCountService

```python
class CycleCountService:
    """Cycle counting operations"""
    
    async def create_count_task(
        self,
        location_id: UUID,
        scheduled_at: datetime,
        count_type: str
    ) -> CycleCount:
        """Create cycle count task"""
        pass
    
    async def record_count(
        self,
        count_item_id: UUID,
        counted_quantity: float,
        user_id: UUID
    ) -> CountResult:
        """
        Record counted quantity
        1. Calculate variance
        2. If variance > 5% → trigger alert
        3. Update article_locations if accepted
        4. Record discrepancy reason
        """
        pass
```

---

### PWA Components (Days 6-8)

#### Location Selection Component

```tsx
// File: frontend/pwa/src/components/LocationPicker.tsx

<TreeSelect
  treeData={locationTree}
  placeholder="Odaberite lokaciju"
  showSearch
  treeDefaultExpandAll
  style={{ width: '100%' }}
  size="large"
  dropdownStyle={{ maxHeight: 400, overflow: 'auto' }}
  treeLine
>
  {/* Tree structure:
    ZONA A
      REGAL A1
        POLICA A1-1
          BIN A1-1-01 🟢
          BIN A1-1-02 🟡
          BIN A1-1-03 🔴
  */}
</TreeSelect>
```

#### Put-Away Page

```tsx
// File: frontend/pwa/src/pages/PutAwayPage.tsx

Layout:
┌──────────────────────────────────┐
│ Odlaganje: RECV-001              │
│ Artikal: 12345 - Test Artikal    │
│ Količina: 100 PCS                │
│                                  │
│ 🤖 Predložena lokacija:          │
│ ┌──────────────────────────────┐│
│ │ ZONA B / REGAL 3 / POLICA 2  ││
│ │ BIN 07                       ││
│ │ Kapacitet: 80% popunjeno     ││
│ │ Udaljenost: 15m              ││
│ │                              ││
│ │ [Prihvati] [Izaberi ručno]  ││
│ └──────────────────────────────┘│
│                                  │
│ Alternative lokacije:            │
│ • ZONA B / R3 / P3 / B08 (85%)  │
│ • ZONA A / R1 / P1 / B02 (60%)  │
└──────────────────────────────────┘

Features:
- AI suggestion with confidence score
- Distance calculation from receiving
- Capacity visualization
- Manual override option
- Alternative suggestions (top 3)
```

#### Picking Route Page

```tsx
// File: frontend/pwa/src/pages/PickingRoutePage.tsx

Layout:
┌──────────────────────────────────┐
│ Zadatak: ZAD-001                 │
│ Tvoja ruta (optimizovano):       │
│                                  │
│ 1️⃣ ZONA A / R1 / P2 / B05  ✅  │
│    12345 - Artikal 1 (10 PCS)   │
│                                  │
│ 2️⃣ ZONA A / R2 / P1 / B03  🔵  │← Current
│    67890 - Artikal 2 (20 PCS)   │
│    [Skeniraj] [Unesi ručno]     │
│                                  │
│ 3️⃣ ZONA B / R3 / P4 / B12  ⬜  │
│    11111 - Artikal 3 (5 PCS)    │
│                                  │
│ Ukupna udaljenost: 45m           │
│ Procijenjeno vrijeme: 12 min     │
└──────────────────────────────────┘
```

#### Cycle Count Page

```tsx
// File: frontend/pwa/src/pages/CycleCountPage.tsx

Layout:
┌──────────────────────────────────┐
│ Popis: ZONA A / REGAL 1          │
│                                  │
│ Artikal: 12345 - Test Artikal    │
│ Lokacija: ZA-R01-P02-B05         │
│                                  │
│ Sistemska količina: 100 PCS      │
│ Prebrojana količina:             │
│   [-] [  ] PCS [+]               │
│                                  │
│ Razlika: 0 PCS (0%)              │
│                                  │
│ [Sačuvaj]                        │
│                                  │
│ ⚠️ Razlika > 5% → Ponovite!     │
└──────────────────────────────────┘
```

---

### Admin UI (Days 9-11)

#### Locations Management Page

```tsx
// File: frontend/admin/src/pages/LocationsPage.tsx

Layout:
┌─────────────────────────────────────────────────────────┐
│ Lokacije - Veleprodajni Magacin                         │
│                                                         │
│ [Tree View] [Map View]  [+ Dodaj zonu]                 │
│                                                         │
│ Tree:                          Details:                 │
│ ┌─────────────────────────┐  ┌──────────────────────┐ │
│ │ 📂 ZONA A         🟢    │  │ BIN A1-1-01          │ │
│ │   📂 REGAL A1     🟡    │  │ Kapacitet: 150 PCS   │ │
│ │     📂 POLICA A1-1 🟡   │  │ Trenutno: 120 PCS    │ │
│ │       📍 BIN A1-1-01 🟡 │  │ Popunjeno: 80%       │ │
│ │       📍 BIN A1-1-02 🟢 │  │                      │ │
│ │       📍 BIN A1-1-03 🔴 │  │ Artikli (3):         │ │
│ │   📂 REGAL A2     🟢    │  │ • 12345 (50 PCS)    │ │
│ │     ...                 │  │ • 67890 (40 PCS)    │ │
│ │ 📂 ZONA B         🟢    │  │ • 11111 (30 PCS)    │ │
│ └─────────────────────────┘  └──────────────────────┘ │
└─────────────────────────────────────────────────────────┘

Features:
- Ant Design Tree component
- Click node → show details in right panel
- Color indicators (🟢 <50%, 🟡 50-90%, 🔴 >90%)
- Drag & drop to reorganize (optional)
- Bulk operations (activate/deactivate)
```

#### Warehouse Map View

```tsx
// File: frontend/admin/src/components/WarehouseMapView.tsx

Layout:
┌─────────────────────────────────────────────────────┐
│ Mapa Magacina - Real-time                           │
│ [Zoom +/-] [Layers: Zones/Bins/Tasks]              │
│                                                     │
│  ┌─────────────────────────────────────────┐       │
│  │                                         │       │
│  │  [ZONA A]          [ZONA B]             │       │
│  │   R1  R2  R3       R1  R2  R3           │       │
│  │   🟢  🟡  🟢       🟡  🔴  🟢           │       │
│  │                                         │       │
│  │  [ZONA C - Receiving]                   │       │
│  │   📦📦📦                                 │       │
│  │                                         │       │
│  └─────────────────────────────────────────┘       │
│                                                     │
│ Legend: 🟢 Dostupno | 🟡 Djelimično | 🔴 Puno     │
│                                                     │
│ Click bin → Show contents                          │
└─────────────────────────────────────────────────────┘

Technology:
- SVG or Canvas rendering
- Real-time occupancy updates (WebSocket)
- Click interaction
- Zoom/Pan controls
- Layer toggles
```

---

### API Endpoints (Day 3-4)

```python
# Locations
GET    /api/locations                       # List all
POST   /api/locations                       # Create zone/regal/polica/bin
GET    /api/locations/{id}                  # Get details
PUT    /api/locations/{id}                  # Update
DELETE /api/locations/{id}                  # Soft delete
GET    /api/locations/tree                  # Hierarchical tree
GET    /api/locations/{id}/articles         # Articles in location
GET    /api/locations/{id}/occupancy        # Capacity stats

# Put-away
POST   /api/receiving/{id}/suggest-location # AI suggestion
POST   /api/receiving/items/{id}/putaway    # Execute putaway
GET    /api/putaway-tasks                   # List pending putaways

# Picking
GET    /api/tasks/{id}/route                # Get pick route
GET    /api/tasks/{id}/next-pick            # Next location in route
POST   /api/tasks/items/{id}/pick-from      # Record pick from location

# Cycle Counting
GET    /api/cycle-counts                    # List counts
POST   /api/cycle-counts                    # Schedule count
GET    /api/cycle-counts/{id}               # Get count detail
POST   /api/cycle-counts/{id}/start         # Start counting
POST   /api/cycle-counts/items/{id}/count   # Record count
POST   /api/cycle-counts/{id}/complete      # Complete count
GET    /api/cycle-counts/discrepancies      # Report

# Map
GET    /api/warehouse-map                   # Get map data
GET    /api/warehouse-map/real-time         # WebSocket stream
```

---

### AI/Heuristic Logic (Day 5)

#### Put-Away Suggestion Algorithm

```python
async def suggest_put_away_location(
    artikal: Artikal,
    quantity: float,
    magacin_id: UUID
) -> List[LocationSuggestion]:
    """
    Score-based location suggestion
    
    Factors:
    1. Zone compatibility (30%)
       - Fast-moving items → Zone A (near dispatch)
       - Slow-moving → Zone C (back)
       - Bulk items → Zone D (high ceiling)
    
    2. Distance from receiving (30%)
       - Closer = better score
       - Calculate Euclidean distance using x,y coordinates
    
    3. Same-class grouping (20%)
       - Prefer bins with same article class
       - Easier to find, reduces travel
    
    4. Capacity match (10%)
       - Prefer bins with capacity > quantity
       - Avoid fragmentation
    
    5. Occupancy balance (10%)
       - Distribute load across regals
       - Avoid overloading single area
    
    Returns: Top 3 locations with scores
    """
    
    # Get candidate bins
    bins = await get_available_bins(magacin_id, min_capacity=quantity)
    
    scores = []
    for bin in bins:
        score = 0
        
        # Zone compatibility
        zone_score = calculate_zone_score(artikal, bin.zona)
        score += zone_score * 0.3
        
        # Distance
        distance = calculate_distance(RECEIVING_ZONE, bin)
        distance_score = 1 / (1 + distance/100)  # Normalize
        score += distance_score * 0.3
        
        # Same-class grouping
        same_class_count = await count_same_class_in_bin(bin, artikal.class)
        grouping_score = min(same_class_count / 5, 1.0)
        score += grouping_score * 0.2
        
        # Capacity match
        capacity_score = 1 - (bin.capacity_current / bin.capacity_max)
        score += capacity_score * 0.1
        
        # Balance
        regal_occupancy = await get_regal_occupancy(bin.parent_id)
        balance_score = 1 - (regal_occupancy / 100)
        score += balance_score * 0.1
        
        scores.append((bin, score))
    
    # Return top 3
    scores.sort(key=lambda x: x[1], reverse=True)
    return [
        LocationSuggestion(
            location_id=bin.id,
            location_code=bin.code,
            score=score,
            distance_meters=calculate_distance(RECEIVING_ZONE, bin),
            current_occupancy=bin.capacity_current / bin.capacity_max * 100
        )
        for bin, score in scores[:3]
    ]
```

#### Picking Route Optimization

```python
async def optimize_pick_route(
    items: List[ZaduznicaStavka]
) -> PickRoute:
    """
    Optimize picking route using nearest-neighbor algorithm
    
    Algorithm:
    1. Start at dispatch zone (0, 0)
    2. Find nearest unpicked item
    3. Add to route, mark as picked
    4. Repeat until all items picked
    5. Return to dispatch
    
    Improvement: TSP (Traveling Salesman) for optimal route
    """
    
    route = []
    current_pos = (0, 0)  # Dispatch zone
    remaining_items = items.copy()
    
    while remaining_items:
        # Find nearest item
        nearest = min(
            remaining_items,
            key=lambda item: distance(current_pos, get_location(item.pick_location_id))
        )
        
        route.append({
            'sequence': len(route) + 1,
            'location_id': nearest.pick_location_id,
            'artikal_id': nearest.artikal_id,
            'quantity': nearest.trazena_kolicina
        })
        
        current_pos = get_location(nearest.pick_location_id).coordinates
        remaining_items.remove(nearest)
    
    total_distance = calculate_route_distance(route)
    estimated_time = (len(route) * 2) + (total_distance / 60)  # 2 min/item + walk time
    
    return PickRoute(
        route_data=route,
        total_distance_meters=total_distance,
        estimated_time_minutes=estimated_time
    )
```

---

### Serbian Language Extensions (Day 1)

```typescript
// File: frontend/pwa/src/i18n/sr-phase3.ts

export const srPhase3 = {
  locations: {
    lokacije: "Lokacije",
    zona: "Zona",
    regal: "Regal",
    polica: "Polica",
    bin: "Bin",
    
    // Hierarchy
    hierarhija: "Hijerarhija",
    odaberiLokaciju: "Odaberite lokaciju",
    
    // Status
    slobodan: "Slobodan",
    djelimicnoZauzet: "Djelimično zauzet",
    pun: "Pun",
    
    // Capacity
    kapacitet: "Kapacitet",
    popunjeno: "Popunjeno",
    dostupno: "Dostupno",
    maksimum: "Maksimum"
  },
  
  putaway: {
    odlaganje: "Odlaganje",
    predloženaLokacija: "Predložena lokacija",
    prihvati: "Prihvati",
    izaberiRucno: "Izaberi ručno",
    alternativneLokacije: "Alternativne lokacije",
    udaljenost: "Udaljenost",
    zapocniOdlaganje: "Započni odlaganje",
    zavrsiOdlaganje: "Završi odlaganje"
  },
  
  picking: {
    tvojaRuta: "Tvoja ruta",
    sljedecaLokacija: "Sljedeća lokacija",
    optimizovano: "Optimizovano",
    ukupnaUdaljenost: "Ukupna udaljenost",
    procijenjeno: "Procijenjeno vrijeme",
    pickIzLokacije: "Preuzmi iz lokacije"
  },
  
  cycleCount: {
    popis: "Popis",
    zakazano: "Zakazano",
    sistemskaKolicina: "Sistemska količina",
    prebrojanakolicina: "Prebrojana količina",
    razlika: "Razlika",
    procenatRazlike: "% razlike",
    upozorenje: "Razlika veća od 5% - Ponovite!",
    razlogRazlike: "Razlog razlike"
  },
  
  map: {
    mapamagacina: "Mapa magacina",
    zoom: "Zumiraj",
    slojevi: "Slojevi",
    zone: "Zone",
    regali: "Regali",
    binovi: "Binovi",
    zadaci: "Zadaci",
    legenda: "Legenda",
    klikniZaDetalje: "Klikni za detalje"
  }
};
```

---

## 🎯 Definition of Done (10 Items)

### 1. ✅ GET /api/locations Returns Full Hierarchy
```bash
curl http://localhost:8123/api/locations/tree
# Expected: Nested JSON with zones → regals → police → bins
```

### 2. ✅ Directed Put-Away Works
```bash
POST /api/receiving/{id}/suggest-location
# Returns: Top 3 suggestions with scores
# Worker can accept or override
```

### 3. ✅ Directed Picking Auto-Generates Route
```bash
GET /api/tasks/{id}/route
# Returns: Optimized sequence (zone → regal → polica → bin)
# Estimated time and distance calculated
```

### 4. ✅ Cycle Count Tasks Work
```bash
POST /api/cycle-counts
GET /api/cycle-counts/{id}
POST /api/cycle-counts/items/{id}/count
# Variance > 5% → alert triggered
```

### 5. ✅ Map View Updates Real-Time
```
Admin → Lokacije → Map View
# Bins change color based on occupancy
# WebSocket updates < 2s
```

### 6. ✅ Team/Shift View on Admin Dashboard
```
Admin → Dashboard → "Aktivne smjene" widget
# Shows Shift A (08-15) workers
# Shows Shift B (12-19) workers
# Shows break periods
```

### 7. ✅ All Endpoints Protected with RBAC
```bash
# Magacioner cannot access admin endpoints
curl -H "Authorization: Bearer $WORKER_TOKEN" /api/locations
# Expected: 200 OK (can view)

curl -X POST -H "Authorization: Bearer $WORKER_TOKEN" /api/locations
# Expected: 403 Forbidden (cannot create)
```

### 8. ✅ TV Shows Real Data (No Mock)
```
TV Dashboard:
- Putaway metrics (avg time, completions)
- Picking metrics (avg time, route efficiency)
- Occupancy by zone
- Cycle count accuracy
```

### 9. ✅ Serbian Language on All New UI
```
All labels, buttons, messages in Serbian:
- Lokacije, Zona, Regal, Polica, Bin
- Odlaganje, Preuzimanje, Popis
- Predložena lokacija, Tvoja ruta
- Sistemska količina, Prebrojana količina
```

### 10. ✅ All Migrations, Tests, Docs Complete
```
- Alembic migrations applied
- Pytest test suite (55+ tests)
- 4 new docs (locations.md, putaway-picking.md, cycle-count.md, map-view.md)
- Sprint summary updated
```

---

## 📊 Implementation Estimates

| Task | Complexity | Est. Time | Files |
|------|-----------|-----------|-------|
| Location schema | High | 1 day | 2 files |
| Location service | High | 2 days | 3 files |
| Put-away AI | High | 1 day | 2 files |
| Picking optimization | High | 1 day | 2 files |
| Cycle count system | Medium | 1 day | 3 files |
| PWA components | High | 3 days | 8 files |
| Admin UI | High | 3 days | 6 files |
| Map view | High | 2 days | 3 files |
| Testing | Medium | 1 day | 2 files |
| Documentation | Medium | 1 day | 4 docs |
| **Total** | | **16 days** | **35+ files** |

---

## 🏗️ Technical Architecture

### Location Storage Strategy

**Physical Hierarchy:**
```
Magacin (Warehouse)
└── Zona A (Zone - receiving area)
    ├── Regal A1 (Rack)
    │   ├── Polica A1-1 (Shelf - level 1)
    │   │   ├── Bin A1-1-01
    │   │   ├── Bin A1-1-02
    │   │   └── Bin A1-1-03
    │   └── Polica A1-2 (Shelf - level 2)
    └── Regal A2
```

**Database Representation:**
```sql
-- Self-referencing hierarchy
parent_id → locations.id

-- Denormalized zona for fast lookup
zona VARCHAR(32)  -- "A", "B", "C"

-- Code format: ZA-R01-P02-B05
-- Zone A, Regal 01, Polica 02, Bin 05
```

---

## 📏 Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| GET /api/locations/tree | <500ms | Full hierarchy |
| POST /api/receiving/{id}/suggest-location | <300ms | AI calculation |
| GET /api/tasks/{id}/route | <400ms | Route optimization |
| POST /api/cycle-counts/items/{id}/count | <200ms | Record count |
| Map view load | <2s | SVG/Canvas rendering |
| Real-time occupancy update | <2s | WebSocket |

---

## 🧪 Test Cases (Add 9 More → Total 55)

**Phase 3 Tests:**
47. Create location hierarchy (zone → bin)
48. Suggest put-away location (AI)
49. Execute put-away (update occupancy)
50. Generate pick route (optimization)
51. Pick from location (sequence)
52. Create cycle count task
53. Record count with variance
54. Alert on variance > 5%
55. Map view real-time update

**Total Test Suite:** 55 test cases

---

**Status:** 🟢 Plan Complete - Ready to Implement  
**Estimated Start:** October 19, 2025  
**Estimated Completion:** November 4, 2025


