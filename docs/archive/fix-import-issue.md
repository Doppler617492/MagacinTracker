# Fix for Import Issue: Excel Files Show "Done" but Don't Appear in Trebovanje/Scheduler

## Problem Analysis

The issue is that Excel files show as "done" after import but the imported trebovanja don't appear in the trebovanje list or scheduler. After investigating, I found the root cause:

**The service user required for import authentication is missing from the database.**

## Root Cause

The import service is configured to authenticate with:
- User ID: `00000000-0000-0000-0000-000000000001`
- Role: `komercijalista`

However, this service user doesn't exist in the database, causing authentication failures.

## Solution

### 1. Immediate Fix - Create Service User

Run one of the following scripts to create the missing service user:

**Option A: Use the updated seed script (recommended)**
```bash
cd backend/services/task_service
python scripts/seed_users_simple.py
```

**Option B: Use the dedicated service user script**
```bash
cd backend/services/task_service  
python scripts/create_service_user.py
```

### 2. Verification Steps

After creating the service user, verify the fix:

1. **Check user exists:**
   ```sql
   SELECT id, email, role FROM users WHERE id = '00000000-0000-0000-0000-000000000001';
   ```

2. **Test import:** Upload a small Excel file and verify:
   - File shows as "done" ✓
   - Trebovanje appears in trebovanje list ✓
   - Trebovanje appears in scheduler ✓

### 3. Files Modified

I've updated the following files to fix this permanently:

1. **`backend/services/task_service/scripts/seed_users_simple.py`** - Added service user to seed data
2. **`backend/services/task_service/scripts/create_service_user.py`** - New script to create just the service user

## Expected Excel Import Format

For reference, the Excel import expects these columns (with various name aliases):

**Required columns:**
- `dokument_broj` (or "broj dokumenta", "broj", "dokument")  
- `datum`
- `magacin` (or "izvor", "magacin naziv")
- `radnja` (or "odredište", "lokacija")
- `artikl_sifra` (or "šifra artikla", "šifra")
- `naziv` (or "naziv artikla")
- `kolicina` (or "količina", "kolicina trazena")

**Optional columns:**
- `barkod` (or "barcode")

## Error Handling Improvement

The current error handling correctly moves failed imports to the failed folder. If you see "done" status, it means the import actually succeeded but the service user was missing, causing a silent authentication failure.

## Next Steps

1. Run one of the scripts above to create the service user
2. Test with a sample Excel file
3. Verify trebovanja appear in both trebovanje list and scheduler
4. The issue should be permanently resolved

## Contact

If you continue to have issues after creating the service user, please check:
1. Database connectivity  
2. Service logs for detailed error messages
3. Excel file format matches expected columns
