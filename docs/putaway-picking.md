# Directed Put-Away & Picking (Vođeno skladištenje i izdavanje)

## Overview

Directed Put-Away and Picking implement Manhattan Active WMS principles for optimized warehouse operations:
- **Put-Away:** AI-powered location suggestions for received goods
- **Picking:** Optimized routes for order fulfillment

---

## 1. Directed Put-Away (Vođeno skladištenje)

### Purpose

Automatically suggest optimal storage locations for received items, maximizing warehouse efficiency and minimizing travel time.

### AI Suggestion Algorithm (5-Factor Scoring)

Each bin is scored 0-100 based on:

#### Factor 1: Zone Compatibility (30 points)
- Match article class to zone type
- **Zone Rules:**
  - **Zona A:** Fast-moving (brza_prodaja, hitno)
  - **Zona B:** Standard (standardno, sezonsko)
  - **Zona C:** Slow-moving (sporo, rezerve)
- **Scoring:** Compatible = 30, Neutral = 10

#### Factor 2: Distance from Dock (20 points)
- Prefer bins closer to receiving area
- Based on X/Y coordinates
- **Scoring:** Near = 20, Medium = 15, Far = 10

#### Factor 3: Available Capacity (20 points)
- Optimal utilization: 50-90% after put-away
- **Scoring:**
  - 50-90% utilization = 20 (optimal)
  - < 50% utilization = 15 (plenty of space)
  - > 90% utilization = 10 (tight fit)

#### Factor 4: Current Occupancy (10 points)
- Prefer bins 30-70% full (consolidation strategy)
- **Scoring:**
  - 30-70% = 10 (good consolidation)
  - < 30% = 5 (empty bin)
  - > 70% = 3

#### Factor 5: Article Consolidation (20 points)
- Bonus for same article already in bin
- **Scoring:** Same article = 20, Different = 0

### API Endpoints

#### Suggest Locations
```http
POST /api/locations/putaway/suggest
Authorization: Bearer <token>
Content-Type: application/json

{
  "artikal_id": "uuid",
  "quantity": 100,
  "uom": "PCS",
  "from_location_id": "uuid"  // Optional: receiving dock
}
```

**Response:**
```json
{
  "artikal_id": "uuid",
  "artikal_sifra": "ART001",
  "artikal_naziv": "Proizvod 1",
  "quantity": 100,
  "suggestions": [
    {
      "location_id": "uuid",
      "location_code": "ZA-R01-P01-B01",
      "location_naziv": "Bin A1-1-01",
      "score": 95.0,
      "distance_meters": 15.5,
      "available_capacity": 80,
      "occupancy_percentage": 45.0,
      "reason": "Kompatibilna zona (A) • Blizu ulaza • Optimalno popunjavanje • Artikal već tu (konsolidacija)"
    },
    // ... up to 5 suggestions
  ]
}
```

#### Execute Put-Away
```http
POST /api/locations/putaway/execute
Authorization: Bearer <token>
Content-Type: application/json

{
  "receiving_item_id": "uuid",
  "location_id": "uuid",
  "quantity": 100,
  "override_suggestion": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Uskladišteno u ZA-R01-P01-B01",
  "article_location_id": "uuid",
  "new_occupancy_percentage": 62.5
}
```

### PWA Workflow

1. **Open Put-Away Task**
   - Navigate from receiving detail
   - See receiving item details (code, name, quantity)

2. **View AI Suggestions**
   - Top 5 locations ranked by score
   - Each card shows:
     - Rank (#1, #2, ...)
     - Location code & name
     - Score out of 100
     - Reason (Serbian)
     - Occupancy & available capacity
   - First suggestion pre-selected

3. **Accept or Override**
   - **Prihvati (Accept):** Use top suggestion
   - **Izaberi ručno (Manual):** Open LocationPicker

4. **Execute**
   - Tap "✅ Potvrdi skladištenje"
   - Article assigned to bin
   - Capacity updated
   - Return to receiving list

### Business Rules

- Only bins (not zones/regals/police) can store articles
- Capacity validation before assignment
- Multiple articles per bin allowed (multi-SKU)
- Primary location flag for main storage
- Audit trail: who, when, which location

---

## 2. Directed Picking (Vođeno izdavanje)

### Purpose

Generate optimized picking routes to minimize travel time and maximize worker productivity.

### Route Optimization Algorithms

#### Nearest Neighbor (Default)
- **Complexity:** O(n²)
- **Performance:** 80-90% optimal
- **Best for:** Any number of items
- **Strategy:**
  1. Start from receiving dock (zone A, lowest X/Y)
  2. Find nearest unpicked location
  3. Repeat until all items picked

#### TSP 2-Opt (Small Batches)
- **Complexity:** O(n²) per iteration
- **Performance:** 95-98% optimal
- **Best for:** ≤10 items
- **Strategy:**
  1. Start with Nearest Neighbor route
  2. Try reversing segments
  3. Keep improvements (limited iterations)

### Distance Calculation

**Manhattan Distance (Grid-Based):**
```
distance = |x1 - x2| + |y1 - y2|
```

**Fallback (No Coordinates):**
- Different zones = 100 units
- Different regals = 20 units
- Same regal = 5 units

### API Endpoints

#### Generate Pick Route
```http
POST /api/locations/pick-routes
Authorization: Bearer <token>
Content-Type: application/json

{
  "zaduznica_id": "uuid",
  "algorithm": "nearest_neighbor"  // or "tsp"
}
```

**Response:**
```json
{
  "zaduznica_id": "uuid",
  "route_id": "uuid",
  "tasks": [
    {
      "stavka_id": "uuid",
      "artikal_sifra": "ART001",
      "artikal_naziv": "Proizvod 1",
      "location_id": "uuid",
      "location_code": "ZA-R01-P01-B01",
      "location_full_path": "ZONA A / REGAL A1 / POLICA A1-1 / BIN A1-1-01",
      "quantity": 10,
      "sequence": 1
    },
    // ... sorted by optimal sequence
  ],
  "total_distance_meters": 145.5,
  "estimated_time_minutes": 20,
  "created_at": "2025-10-19T10:00:00Z"
}
```

#### Get Existing Route
```http
GET /api/locations/pick-routes/{zaduznica_id}
Authorization: Bearer <token>
```

Returns same structure as generate (idempotent).

### PWA Workflow

1. **Open Zaduznica**
   - Tap zaduznica from list
   - Auto-generate route on first access

2. **View Route**
   - Progress bar (X / Y završeno)
   - Estimated time & distance
   - Current task (huge font):
     - Location code (32px, blue)
     - Full path breadcrumb
     - Article code & name
     - Quantity to pick
     - Sequence number (#1, #2, ...)

3. **Pick Item**
   - Tap "✅ Završi stavku"
   - Mark as completed
   - Auto-jump to next location

4. **Navigate**
   - See remaining tasks list
   - Tap any task to jump
   - Completed tasks shown with ✓

### Database Updates

**`zaduznica_stavka` Extensions:**
- `pick_location_id` - Assigned bin
- `pick_sequence` - Optimal order (1, 2, 3, ...)
- `picked_at` - Completion timestamp

**`pick_routes` Table:**
- `zaduznica_id` - Reference
- `route_data` - JSON array of sequence
- `total_distance_meters` - Calculated distance
- `estimated_time_minutes` - 2 min per pick
- `actual_time_minutes` - Real completion time

### Performance Benchmarks

| Items | Algorithm | Generation Time | Quality |
|-------|-----------|----------------|---------|
| 5     | Nearest   | < 50ms         | 85%     |
| 10    | TSP       | < 200ms        | 95%     |
| 20    | Nearest   | < 100ms        | 80%     |
| 50    | Nearest   | < 250ms        | 75%     |

**P95 Target:** < 250ms for route generation

---

## RBAC Access Control

| Role | Put-Away | Picking | Route Generation |
|------|----------|---------|-----------------|
| ADMIN | ✅ | ✅ | ✅ |
| MENADŽER | ✅ | ✅ | ✅ |
| ŠEF | ✅ | ✅ | ✅ |
| MAGACIONER | ✅ | ✅ | ❌ |
| KOMERCIJALISTA | ❌ | ❌ | ❌ |

---

## Metrics & KPIs

**Put-Away Metrics:**
- Avg put-away time (goal: < 3 min)
- Suggestion acceptance rate (goal: > 80%)
- Manual override rate (goal: < 20%)
- Capacity utilization (goal: 60-80%)

**Picking Metrics:**
- Avg pick time per item (goal: < 2 min)
- Route completion time
- Route efficiency (actual vs. estimated)
- Items picked per hour (goal: > 30)

---

## Testing

See `test-report-phase3.md` for:
- Put-away suggestion tests (5 scenarios)
- Route optimization tests (3 algorithms)
- Distance calculation tests
- Performance benchmarks

