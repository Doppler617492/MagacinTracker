# UoM / Case-Pack Conversion - Documentation

**Feature:** Sprint WMS Phase 2  
**Purpose:** Consistent quantity handling across all processes  
**Language:** Serbian (Srpski)

---

## Overview

The UoM (Unit of Measure) / Case-Pack system ensures consistent quantity handling throughout the WMS:

**Core Principle:** 
> All quantities are **stored in base_uom** (typically PCS - pieces)  
> Display can show **pack_uom** (BOX, CASE) as convenience  
> All calculations, KPIs, and exports use **base_uom**

---

## Terminology

| Term | Serbian | Example | Description |
|------|---------|---------|-------------|
| **base_uom** | Osnovna jedinica | PCS (komad) | Primary unit for storage |
| **pack_uom** | Jedinica pakovanja | BOX (kutija) | Packaging unit |
| **conversion_factor** | Faktor konverzije | 12 | How many base units per pack |

---

## Article Configuration

### Example: Coca Cola 0.5L

```sql
INSERT INTO artikal (sifra, naziv, base_uom, pack_uom, conversion_factor)
VALUES ('COCA-05', 'Coca Cola 0.5L', 'PCS', 'BOX', 12);

-- Meaning:
-- 1 BOX = 12 PCS
-- 24 BOX = 288 PCS
```

### Database Schema

```sql
ALTER TABLE artikal
ADD COLUMN base_uom VARCHAR(32) DEFAULT 'PCS',
ADD COLUMN pack_uom VARCHAR(32),
ADD COLUMN conversion_factor NUMERIC(8,3),
ADD COLUMN is_primary_pack BOOLEAN DEFAULT false;

-- Constraint: factor must be positive
ALTER TABLE artikal
ADD CONSTRAINT ck_conversion_factor_positive
CHECK (conversion_factor IS NULL OR conversion_factor > 0);
```

---

## Conversion Rules

### Rule 1: Import Conversion

**When importing documents:**
```python
# CSV has quantity in BOX
row = {"kolicina": 24, "jedinica_mjere": "BOX"}

# Article config
article = {
  "base_uom": "PCS",
  "pack_uom": "BOX",
  "conversion_factor": 12
}

# Convert to base_uom before storing
if row["jedinica_mjere"] == article["pack_uom"]:
    kolicina_pcs = row["kolicina"] * article["conversion_factor"]
    # 24 BOX * 12 = 288 PCS
else:
    kolicina_pcs = row["kolicina"]

# Store in database
trebovanje_stavka.kolicina_trazena = kolicina_pcs  # 288 PCS
trebovanje_stavka.jedinica_mjere = article["base_uom"]  # PCS
```

### Rule 2: Display Conversion

**When showing to users:**
```python
# Database has: 288 PCS
quantity_pcs = 288

# Option A: Show base only
display = f"{quantity_pcs} PCS"
→ "288 PCS"

# Option B: Show with pack equivalent
quantity_box = quantity_pcs / conversion_factor  # 288 / 12 = 24
display = f"{quantity_pcs} PCS ({quantity_box} BOX)"
→ "288 PCS (24 BOX)"
```

### Rule 3: PWA Entry

**Workers always enter in base_uom:**
```
Screen shows:
  Traženo: 288 PCS (24 BOX)  ← Info only
  Primljeno: [stepper] PCS    ← Entry in PCS
  
Worker enters: 276 PCS
System calculates: 23 BOX (276 / 12)
Variance: -12 PCS (-1 BOX)
```

### Rule 4: KPI & Reports

**All analytics use base_uom:**
```sql
-- KPI Query - Always in PCS
SELECT 
  SUM(kolicina_trazena) as total_trazeno_pcs,
  SUM(kolicina_primljena) as total_primljeno_pcs,
  (SUM(kolicina_primljena) / SUM(kolicina_trazena) * 100) as procenat
FROM receiving_item;

-- Result: 
-- total_trazeno_pcs: 1000 PCS
-- total_primljeno_pcs: 950 PCS
-- procenat: 95%
```

---

## Implementation

### UoMConversionService

```python
class UoMConversionService:
    async def convert_to_base_uom(self, quantity, uom, article) -> Decimal:
        """Convert BOX → PCS"""
        if uom == article.base_uom:
            return quantity
        
        if uom == article.pack_uom:
            return quantity * article.conversion_factor
        
        raise ValueError(f"Unknown UoM: {uom}")
    
    async def convert_from_base_uom(self, quantity, target_uom, article) -> Decimal:
        """Convert PCS → BOX"""
        if target_uom == article.base_uom:
            return quantity
        
        if target_uom == article.pack_uom:
            return quantity / article.conversion_factor
        
        raise ValueError(f"Unknown UoM: {target_uom}")
```

### Usage in Import

```python
# Import service
async def import_receiving(file):
    for row in rows:
        artikal = await get_artikal(row['sifra'])
        
        # Convert to base_uom
        quantity_base = await uom_service.convert_to_base_uom(
            quantity=row['kolicina'],
            uom=row['jedinica_mjere'],
            article=artikal
        )
        
        # Store in base_uom
        item = ReceivingItem(
            sifra=row['sifra'],
            kolicina_trazena=quantity_base,  # Always PCS
            jedinica_mjere=artikal.base_uom  # Always PCS
        )
```

---

## Common Scenarios

### Scenario 1: Full Case Receipt
```
Expected: 24 BOX (288 PCS)
Received: 24 BOX (288 PCS)
Variance: 0
Status: Završeno (full)
```

### Scenario 2: Partial Box
```
Expected: 24 BOX (288 PCS)
Received: 23.5 BOX (282 PCS)
Variance: -6 PCS
Razlog: "Oštećeno"
Status: Završeno (djelimično)
```

### Scenario 3: Overage
```
Expected: 24 BOX (288 PCS)
Received: 25 BOX (300 PCS)
Variance: +12 PCS (+1 BOX)
Razlog: "Višak"
Status: Završeno (djelimično)
```

### Scenario 4: Damaged Box
```
Expected: 24 BOX (288 PCS)
Received: 23 BOX (276 PCS) + 6 PCS loose
Total: 282 PCS
Variance: -6 PCS
Razlog: "Oštećeno"
Napomena: "Jedna kutija oštećena, primljeno samo 6 komada iz nje"
Photos: 2 (damaged box + loose items)
```

---

## Validation

### Import Validation
```python
# Check UoM matches article config
if row['jedinica_mjere'] not in [article.base_uom, article.pack_uom]:
    raise ValueError(
        f"Jedinica mjere '{row['jedinica_mjere']}' nije validna. "
        f"Očekivano: {article.base_uom} ili {article.pack_uom}"
    )

# Check conversion factor exists if using pack_uom
if row['jedinica_mjere'] == article.pack_uom and not article.conversion_factor:
    raise ValueError(
        f"Artikal {article.sifra} nema faktor konverzije za {article.pack_uom}"
    )
```

---

## Admin Catalog Management

### Edit Article UoM
```tsx
<Form>
  <Form.Item label="Osnovna jedinica" required>
    <Select value={article.base_uom}>
      <Option value="PCS">PCS (komad)</Option>
      <Option value="LIT">LIT (litar)</Option>
      <Option value="KG">KG (kilogram)</Option>
    </Select>
  </Form.Item>
  
  <Form.Item label="Jedinica pakovanja">
    <Select value={article.pack_uom}>
      <Option value="">Nema</Option>
      <Option value="BOX">BOX (kutija)</Option>
      <Option value="CASE">CASE (gajba)</Option>
      <Option value="PALLET">PALLET (paleta)</Option>
    </Select>
  </Form.Item>
  
  {article.pack_uom && (
    <Form.Item 
      label="Faktor konverzije" 
      required
      help={`Koliko ${article.base_uom} u 1 ${article.pack_uom}`}
    >
      <InputNumber 
        min={0.001}
        precision={3}
        placeholder="npr. 12"
      />
    </Form.Item>
  )}
</Form>
```

---

## Testing

### Test Case 1: BOX to PCS Conversion
```python
async def test_box_to_pcs():
    article = Artikal(
        sifra="TEST",
        base_uom="PCS",
        pack_uom="BOX",
        conversion_factor=12
    )
    
    result = await uom_service.convert_to_base_uom(
        quantity=Decimal("24"),
        uom="BOX",
        article=article
    )
    
    assert result == Decimal("288")  # 24 * 12
```

### Test Case 2: PCS to BOX Conversion
```python
async def test_pcs_to_box():
    article = Artikal(
        sifra="TEST",
        base_uom="PCS",
        pack_uom="BOX",
        conversion_factor=12
    )
    
    result = await uom_service.convert_from_base_uom(
        quantity=Decimal("288"),
        target_uom="BOX",
        article=article
    )
    
    assert result == Decimal("24")  # 288 / 12
```

### Test Case 3: Import with BOX
```python
async def test_import_with_box():
    # Import CSV with BOX quantities
    file_content = """
broj_prijema,sifra,kolicina,jedinica_mjere
RECV-001,COCA-05,24,BOX
"""
    
    # After import
    item = await db.get_receiving_item(...)
    
    # Should be converted to PCS
    assert item.kolicina_trazena == 288  # 24 * 12
    assert item.jedinica_mjere == "PCS"
```

---

## Migration Path

**Existing Data:**
```sql
-- Set default base_uom for all existing articles
UPDATE artikal SET base_uom = 'PCS' WHERE base_uom IS NULL;

-- For articles known to be packaged:
UPDATE artikal 
SET pack_uom = 'BOX', conversion_factor = 12
WHERE sifra IN ('COCA-05', 'PEPSI-05', ...);
```

**New Articles:**
```sql
-- Always specify UoM on creation
INSERT INTO artikal (sifra, naziv, base_uom, pack_uom, conversion_factor)
VALUES ('NEW-123', 'New Product', 'PCS', 'BOX', 12);
```

---

## FAQ

**Q: Can an article have multiple pack sizes?**  
A: Not in Phase 2. Only one pack_uom per article. Future: support multiple (CASE=24, PALLET=288).

**Q: What if worker receives partial boxes?**  
A: Enter in PCS. Example: 23.5 BOX = 282 PCS (23 * 12 + 6).

**Q: Do all articles need pack_uom?**  
A: No. Articles without packaging (loose items) only need base_uom.

**Q: Can base_uom be changed?**  
A: Risky. Would require data migration. Plan carefully.

**Q: What about weight-based items (KG)?**  
A: Use base_uom='KG', no pack_uom unless packaged in bags/boxes.

---

**Document Version:** 1.0  
**Last Updated:** October 19, 2025  
**Status:** ✅ Documented


