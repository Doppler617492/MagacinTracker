# AI Bin Allocation (AI dodjela bin lokacija)

## Overview

AI-powered bin allocation uses a 5-factor scoring algorithm to suggest optimal storage locations for received goods, maximizing warehouse efficiency and minimizing travel time.

## Purpose

- **Reduce put-away time** by suggesting nearest optimal locations
- **Maximize space utilization** with smart capacity planning
- **Enable article consolidation** by preferring bins with same article
- **Improve pick efficiency** by placing fast-movers near entrance

## 5-Factor Scoring Algorithm

Each bin is scored 0-100 based on:

### Factor 1: Zone Compatibility (30 points)

**Purpose:** Match article class to appropriate zone

**Zone Rules:**
- **Zona A:** Fast-moving (brza_prodaja, hitno)
- **Zona B:** Standard (standardno, sezonsko)
- **Zona C:** Slow-moving (sporo, rezerve)

**Scoring:**
- Compatible class: 30 points
- Neutral/default: 10 points

**Example:**
- Article class "brza_prodaja" → Zona A = 30 pts
- Article class "sporo" → Zona C = 30 pts
- Article class "default" → any zone = 10 pts

### Factor 2: Distance from Dock (20 points)

**Purpose:** Minimize travel distance from receiving area

**Distance Categories:**
- **Near:** Zona A, X < 20 → 20 points
- **Medium:** Zona B → 15 points
- **Far:** Zona C or X ≥ 20 → 10 points

**Note:** Uses X/Y coordinates if available, otherwise zone-based heuristic

### Factor 3: Available Capacity (20 points)

**Purpose:** Optimize bin fill rate

**Utilization Scoring:**
- **Optimal (50-90%):** 20 points — Good utilization
- **Plenty (<50%):** 15 points — Lots of space
- **Tight (>90%):** 10 points — Tight but fits

**Formula:**
```
utilization = quantity_to_store / available_capacity
```

### Factor 4: Current Occupancy (10 points)

**Purpose:** Prefer bins 30-70% full for consolidation

**Occupancy Scoring:**
- **30-70% full:** 10 points — Good consolidation
- **< 30% full:** 5 points — Empty bin
- **> 70% full:** 3 points — Nearly full

### Factor 5: Article Consolidation (20 points)

**Purpose:** Keep same articles together

**Scoring:**
- **Same article already in bin:** 20 points
- **Different article:** 0 points

**Benefit:** Faster picking, easier cycle counting

## API Endpoints

### Suggest Bins

```http
POST /api/ai/bin-suggest
Authorization: Bearer <token>
Content-Type: application/json

{
  "receiving_item_id": "uuid",
  "artikal_id": "uuid",
  "quantity": 100,
  "magacin_id": "uuid"
}
```

**Response:**
```json
{
  "suggestions": [
    {
      "rank": 1,
      "location_id": "uuid",
      "location_code": "ZA-R01-P01-B01",
      "location_path": "ZONA A / REGAL A1 / POLICA A1-1 / BIN A1-1-01",
      "score": 95.0,
      "confidence": 0.95,
      "reason": "Kompatibilna zona (A) • Blizu ulaza • Optimalno popunjavanje • Artikal već tu (konsolidacija)",
      "available_capacity": 80.0,
      "occupancy_percentage": 45.0
    },
    // ... up to 3 suggestions
  ],
  "model_version": "heuristic_v1",
  "latency_ms": 180
}
```

### Accept Suggestion

```http
POST /api/ai/bin-accept
Authorization: Bearer <token>
Content-Type: application/json

{
  "receiving_item_id": "uuid",
  "location_id": "uuid"
}
```

**Action:** Marks suggestion as accepted, creates audit log

### Reject Suggestion

```http
POST /api/ai/bin-reject
Authorization: Bearer <token>
Content-Type: application/json

{
  "receiving_item_id": "uuid",
  "reason": "Lokacija predaleko od ulaza"
}
```

**Action:** Marks all suggestions as rejected with reason

## PWA Workflow

### 1. Complete Receiving Item Entry

Worker enters received quantity, reason, photos on `ReceivingDetailPage`.

### 2. AI Suggestion Panel Appears

After quantity entry, panel shows:
- **Top suggestion** (rank #1) with large display
- **Score** (0-100)
- **Confidence** (0-1.0)
- **Reason** in Serbian (multi-line)
- **Occupancy** and **available capacity**

### 3. Worker Actions

**Option A: Prihvati (Accept)**
- Tap "✅ Prihvati predlog"
- Executes put-away to suggested bin
- Updates article_locations
- Toast: "Predlog prihvaćen - uskladišteno u ZA-R01-P01-B01"

**Option B: Prikaži još (Show more)**
- Expands to show all 3 suggestions
- Worker can tap any of the 3
- Same accept flow

**Option C: Odbij i izaberi ručno (Reject + manual)**
- Tap "📍 Izaberi ručno"
- Opens LocationPicker (tree selector)
- Worker manually selects bin
- Marks suggestions as rejected

### 4. Offline Handling

- If offline, suggestion request queued
- Worker sees "Offline - čeka se konekcija"
- On reconnect, suggestions load automatically

## Admin UI

### AI Bin Allocation Log

**Path:** Admin → AI → Bin Allocation Log

**Features:**
- Table with columns:
  - Date/Time
  - Receiving Item (broj + stavka)
  - Article (code + name)
  - Suggested Location (top 1)
  - Score
  - Outcome (Accepted / Rejected)
  - Accepted By
  - Rejection Reason
- Filters:
  - Date range
  - Article (autocomplete)
  - Zone
  - Outcome (accepted/rejected/pending)
- Metrics:
  - Acceptance rate (target: > 80%)
  - Avg score of accepted suggestions
  - Top 5 rejected reasons

**Export:** CSV with all fields

## Metrics & KPIs

### Suggestion Quality
- **Acceptance rate:** `accepted / total * 100%`
  - Target: > 80%
- **Avg score of accepted:** Target: > 85/100
- **Manual override rate:** Target: < 20%

### Performance
- **P95 latency:** Target: ≤ 350ms
- **P99 latency:** Target: ≤ 500ms

### Business Impact
- **Avg put-away time:** Before vs After AI (target: 30% reduction)
- **Space utilization:** Target: 60-80% across all bins
- **Consolidation rate:** % of articles with single primary location

## Audit Trail

All actions logged with `AuditAction`:
- `AI_BIN_SUGGESTED` - Suggestions generated
- `AI_BIN_ACCEPTED` - Worker accepted suggestion
- `AI_BIN_REJECTED` - Worker rejected and chose manual

**Audit fields:**
- `user_id` - Worker who acted
- `entity_id` - Suggestion ID
- `details` - JSON with location, score, rank, reason

## Model Versioning

Current model: **heuristic_v1**

**Parameters:**
```json
{
  "weights": {
    "zone_compatibility": 30.0,
    "distance": 20.0,
    "capacity": 20.0,
    "occupancy": 10.0,
    "consolidation": 20.0
  },
  "zone_rules": {
    "A": ["brza_prodaja", "hitno", "default"],
    "B": ["standardno", "sezonsko", "default"],
    "C": ["sporo", "rezerve", "default"]
  }
}
```

**Performance Metrics:**
- Tracked in `ai_model_metadata` table
- Updated weekly with acceptance rates and latency

## Feature Flag

**Environment Variable:** `FF_AI_BIN_ALLOCATION=true`

**Behavior when disabled:**
- API returns 404 "AI Bin Allocation nije omogućen"
- PWA shows manual LocationPicker only
- No suggestions generated

## RBAC Access

| Role | Suggest | Accept | Reject | View Log |
|------|---------|--------|--------|----------|
| ADMIN | ✅ | ✅ | ✅ | ✅ |
| MENADŽER | ✅ | ✅ | ✅ | ✅ |
| ŠEF | ✅ | ✅ | ✅ | ✅ |
| MAGACIONER | ✅ | ✅ | ✅ | ❌ |
| KOMERCIJALISTA | ❌ | ❌ | ❌ | ❌ |

## Testing

See `test-report-phase4.md` for:
- Suggestion generation tests (5 scenarios)
- Accept/reject workflow tests
- Score calculation tests
- Latency benchmarks
- Offline handling tests

## Future Enhancements (Phase 5)

- **Machine Learning model** trained on historical acceptance data
- **Real-time coordinates** from worker devices for distance calculation
- **Dynamic weights** based on warehouse performance
- **Multi-criteria optimization** (pick route + put-away combined)
- **Predictive slotting** (auto-suggest bin reassignments)

