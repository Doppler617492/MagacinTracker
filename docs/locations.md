# Warehouse Locations (Lokacije magacina)

## Overview

The Location system implements a hierarchical warehouse topology based on Manhattan Active WMS patterns, enabling precise inventory tracking and directed operations.

## Hierarchy Structure

```
ZONA (Zone)
└── REGAL (Rack/Aisle)
    └── POLICA (Shelf)
        └── BIN (Storage Unit)
```

### Location Types

1. **Zona (Zone)**
   - Top-level warehouse area
   - Used for high-level organization
   - Example: "Zona A" (fast-moving items)

2. **Regal (Rack/Aisle)**
   - Physical rack or aisle within a zone
   - Example: "Regal A1", "Regal A2"

3. **Polica (Shelf)**
   - Shelf level within a rack
   - Example: "Polica A1-1", "Polica A1-2"

4. **Bin (Storage Unit)**
   - Smallest storage unit (pick/put location)
   - Example: "Bin A1-1-01", "Bin A1-1-02"
   - **Workers interact only with bins**

## Features

### 1. Location Management (Admin)

**Access:** Admin, Menadžer

**API Endpoints:**
- `GET /api/locations` - List locations with filters
- `GET /api/locations/tree` - Hierarchical tree structure
- `GET /api/locations/{id}` - Location details
- `POST /api/locations` - Create location
- `PUT /api/locations/{id}` - Update location
- `DELETE /api/locations/{id}` - Soft delete location

**Admin UI:**
- Tree view with expand/collapse
- Color-coded by type (Blue/Green/Orange/Purple)
- Status indicators (🟢🟡🔴) based on occupancy
- Location details panel:
  - Name, code, zone
  - Capacity (current / max)
  - Occupancy percentage
  - Coordinates (X, Y) for map
- Articles in location table
- Create location modal

### 2. Article Location Tracking

**Database:** `article_locations` table

**Fields:**
- `artikal_id` - Article reference
- `location_id` - Bin reference
- `quantity` - Current stock quantity
- `uom` - Unit of measure
- `is_primary_location` - Primary storage flag
- `last_counted_at` - Last cycle count timestamp
- `last_moved_at` - Last movement timestamp

**Features:**
- Multi-SKU bins (one bin, multiple articles)
- Primary vs. secondary locations
- Quantity tracking per bin
- Movement history

**API Endpoints:**
- `GET /api/locations/{id}/articles` - Articles in location
- `POST /api/locations/articles` - Assign article to location

### 3. Capacity Management

**Capacity Tracking:**
- `capacity_max` - Maximum capacity (optional)
- `capacity_current` - Current usage
- `occupancy_percentage` - Calculated (current / max * 100)

**Status Colors:**
- 🟢 Green: < 50% (Slobodno)
- 🟡 Yellow: 50-90% (Delimično zauzeto)
- 🔴 Red: ≥ 90% (Puno)

**Validation:**
- Cannot assign article if `capacity_current + quantity > capacity_max`
- Cannot delete location with inventory (must move articles first)

## Location Codes

**Naming Convention:**
- Zone: `ZA`, `ZB`, `ZC`
- Regal: `ZA-R01`, `ZA-R02`
- Polica: `ZA-R01-P01`, `ZA-R01-P02`
- Bin: `ZA-R01-P01-B01`, `ZA-R01-P01-B02`

**Properties:**
- Unique across warehouse
- Human-readable
- Hierarchical structure visible

## Seed Data (Example)

The system seeds with example structure:

```
Veleprodajni Magacin
├── Zona A (10000 capacity)
│   ├── Regal A1 (1000 capacity)
│   │   ├── Polica A1-1 (500 capacity)
│   │   │   ├── Bin A1-1-01 (100 capacity)
│   │   │   ├── Bin A1-1-02 (100 capacity)
│   │   │   ├── Bin A1-1-03 (100 capacity)
│   │   │   ├── Bin A1-1-04 (100 capacity)
│   │   │   └── Bin A1-1-05 (100 capacity)
│   │   └── Polica A1-2 (500 capacity)
│   │       ├── Bin A1-2-01 (100 capacity)
│   │       ├── Bin A1-2-02 (100 capacity)
│   │       └── Bin A1-2-03 (100 capacity)
│   └── Regal A2 (1000 capacity)
└── Zona B (8000 capacity)
```

## Database Schema

```sql
CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    naziv VARCHAR(128) NOT NULL,
    code VARCHAR(32) UNIQUE NOT NULL,
    tip location_type_enum NOT NULL,  -- zone, regal, polica, bin
    parent_id UUID REFERENCES locations(id),
    magacin_id UUID REFERENCES magacin(id) NOT NULL,
    zona VARCHAR(32),  -- Denormalized for fast lookup
    x_coordinate NUMERIC(8,2),
    y_coordinate NUMERIC(8,2),
    capacity_max NUMERIC(12,3),
    capacity_current NUMERIC(12,3) DEFAULT 0,
    is_active BOOLEAN DEFAULT true,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE article_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    artikal_id UUID REFERENCES artikal(id) NOT NULL,
    location_id UUID REFERENCES locations(id) NOT NULL,
    quantity NUMERIC(12,3) DEFAULT 0,
    uom VARCHAR(32) DEFAULT 'PCS',
    last_counted_at TIMESTAMP WITH TIME ZONE,
    last_moved_at TIMESTAMP WITH TIME ZONE,
    is_primary_location BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(artikal_id, location_id)
);
```

## RBAC Access Control

| Role | View | Create | Update | Delete | Assign Articles |
|------|------|--------|--------|--------|----------------|
| ADMIN | ✅ | ✅ | ✅ | ✅ | ✅ |
| MENADŽER | ✅ | ✅ | ✅ | ❌ | ✅ |
| ŠEF | ✅ | ❌ | ❌ | ❌ | ✅ |
| MAGACIONER | ✅ | ❌ | ❌ | ❌ | ✅ |
| KOMERCIJALISTA | ❌ | ❌ | ❌ | ❌ | ❌ |

## Related Features

- **Put-Away:** Uses locations for directed storage (see `putaway-picking.md`)
- **Picking:** Generates routes based on location coordinates (see `putaway-picking.md`)
- **Cycle Counting:** Verifies inventory by location (see `cycle-count.md`)
- **Warehouse Map:** 2D visualization of locations (Admin/TV)

## Performance

- Indexed fields: `parent_id`, `magacin_id`, `zona`, `tip`, `code`
- Denormalized `zona` for fast filtering
- Tree queries optimized with CTE (Common Table Expressions)
- Capacity updates in same transaction as article assignment

## Migration

Run Alembic migration:
```bash
alembic upgrade head
```

Revision: `20251019_locations`

## Testing

See `test-report-phase3.md` for:
- Location CRUD tests
- Hierarchy tests
- Capacity validation tests
- Article assignment tests

