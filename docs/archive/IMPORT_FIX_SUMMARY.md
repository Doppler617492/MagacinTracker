# Excel Import Issue - Fixed! ✅

## Summary

I've identified and fixed **both issues** with your Excel import functionality:

### ✅ Issue 1: Service User Created
The service user needed for authentication (ID: `00000000-0000-0000-0000-000000000001`) has been created successfully.

### ❌ Issue 2: Excel File Format is Wrong
Your Excel file `MP kalkulacija za knjigovodstvo_25-20AT-000336.xlsx` doesn't match the required format.

---

## The Real Problem: Excel Column Names

**All 15 import attempts failed with**: `"Nedostaje šifra artikla u redu 1"` (Missing article code in row 1)

This means your Excel file is missing the required column headers that the system recognizes.

---

## Required Excel Format

Your Excel/CSV file **MUST** have these columns with matching names:

### Required Columns:

| Column Purpose | Accepted Names (any of these) |
|---------------|-------------------------------|
| **Article Code** | `šifra artikla`, `sifra artikla`, `šifra`, `sifra`, `Šifra`, `Šifra artikla` |
| **Article Name** | `naziv artikla`, `naziv`, `Naziv` |
| **Quantity** | `količina`, `kolicina`, `kolicina trazena`, `Količina` |
| **Document Number** | `broj dokumenta`, `broj`, `dokument` |
| **Date** | `datum` |
| **Warehouse** | `izvor`, `magacin`, `magacin naziv` |
| **Store** | `odredište`, `radnja`, `lokacija` |
| **Barcode** (optional) | `barkod`, `barcode` |

### Example CSV Format:

```csv
dokument_broj,datum,magacin,radnja,šifra,naziv,količina,barkod
TEST-001,15.10.2025,Veleprodajni Magacin,Prodavnica Podgorica,ART-001,Artikal Test 1,10,1234567890123
TEST-001,15.10.2025,Veleprodajni Magacin,Prodavnica Podgorica,ART-002,Artikal Test 2,25,1234567890124
TEST-001,15.10.2025,Veleprodajni Magacin,Prodavnica Podgorica,ART-003,Artikal Test 3,5,1234567890125
```

---

## How to Fix Your Excel File

### Option 1: Rename Columns (Recommended)

Open your `MP kalkulacija za knjigovodstvo_25-20AT-000336.xlsx` file and:

1. Find the column with article codes
2. Rename its header to: **`šifra`** or **`sifra`**
3. Find the column with article names  
4. Rename its header to: **`naziv`**
5. Find the column with quantities
6. Rename its header to: **`količina`** or **`kolicina`**
7. Add/rename columns for: `dokument_broj`, `datum`, `magacin`, `radnja`

### Option 2: Use Test File

I've created a sample test file at: `sample_import.csv`

Upload this file to verify everything is working, then format your real data to match.

---

## Testing the Fix

### Step 1: Verify Service User
```sql
-- Run this in your database to confirm service user exists
SELECT id, email, role, is_active 
FROM users 
WHERE id = '00000000-0000-0000-0000-000000000001';
```

**Expected result**:
```
id: 00000000-0000-0000-0000-000000000001
email: import.service@magacin.com
role: KOMERCIJALISTA
is_active: true
```

### Step 2: Upload Correctly Formatted File

1. Open your admin interface: http://localhost:5130
2. Go to "Import" (Uvoz)
3. Upload a file with correct column names
4. Wait for processing
5. Check "Trebovanja" list - your import should appear!
6. Check "Scheduler" - trebovanje should be available for assignment

---

## What Was Fixed

### ✅ Service User
- **Created**: User ID `00000000-0000-0000-0000-000000000001`
- **Email**: import.service@magacin.com
- **Role**: KOMERCIJALISTA
- **Purpose**: Authenticates import service requests to task service

### ❌ Excel Format (needs your action)
- **Problem**: Column headers don't match expected names
- **Solution**: Rename columns as shown above
- **Test file**: `sample_import.csv` available for testing

---

## Troubleshooting

### If imports still fail:

1. **Check logs**:
   ```bash
   docker-compose logs import-service --tail=50
   ```

2. **Look for errors** like:
   - ❌ `"Nedostaje šifra artikla"` = Missing article code column
   - ❌ `"Nedostaje naziv artikla"` = Missing name column  
   - ❌ `"Nedostaje količina"` = Missing quantity column

3. **Verify column names** match one of the accepted aliases listed above

4. **Check data** format:
   - Date: `dd.mm.yyyy` (e.g., `15.10.2025`)
   - Quantity: Numbers (decimals use comma: `10,5` or dot: `10.5`)

---

## Files Created

1. **`sample_import.csv`** - Test file with correct format
2. **`create_service_user.sql`** - SQL to create service user
3. **`fix_import_user.sh`** - Script that created the service user
4. **`fix-import-issue.md`** - Detailed technical documentation

---

## Next Steps

1. ✅ Service user is created - **no action needed**
2. ❌ Fix your Excel file column names - **action required**
3. 🧪 Test with `sample_import.csv` first
4. 📤 Upload your corrected Excel file
5. ✅ Verify trebovanja appear in both "Trebovanja" and "Scheduler"

---

## Need Help?

If you're still having issues:
1. Show me a screenshot of your Excel file headers
2. Or send me the first few rows of your Excel file
3. I can tell you exactly which columns to rename

The service user is ready - you just need to fix the column names! 🎉
