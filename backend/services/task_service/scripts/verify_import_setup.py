#!/usr/bin/env python3
"""
Verify that the import setup is correct and service user exists.
Run with: python scripts/verify_import_setup.py
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app_common.config import get_settings

settings = get_settings()

async def verify_import_setup():
    """Verify that all components needed for import are properly set up"""
    engine = create_async_engine(settings.database_url)
    
    print("🔍 Verifying import setup...")
    
    async with engine.connect() as conn:
        
        # 1. Check service user exists
        print("\n1. Checking service user...")
        result = await conn.execute(
            text("SELECT id, email, role, is_active FROM users WHERE id = :service_user_id"),
            {"service_user_id": "00000000-0000-0000-0000-000000000001"}
        )
        service_user = result.fetchone()
        
        if service_user:
            print(f"✅ Service user found:")
            print(f"   ID: {service_user[0]}")
            print(f"   Email: {service_user[1]}")
            print(f"   Role: {service_user[2]}")
            print(f"   Active: {service_user[3]}")
        else:
            print("❌ Service user NOT found!")
            print("   Run: python scripts/seed_users_simple.py")
            print("   Or: python scripts/create_service_user.py")
            return False
        
        # 2. Check service user role is correct
        if service_user[2] != "komercijalista":
            print(f"❌ Service user has wrong role: {service_user[2]} (expected: komercijalista)")
            return False
        
        if not service_user[3]:
            print("❌ Service user is not active!")
            return False
        
        # 3. Check recent trebovanja
        print("\n2. Checking recent trebovanja...")
        result = await conn.execute(
            text("""
                SELECT COUNT(*) as total, 
                       COUNT(CASE WHEN created_at > NOW() - INTERVAL '24 hours' THEN 1 END) as recent
                FROM trebovanje
            """)
        )
        trebovanje_stats = result.fetchone()
        
        print(f"   Total trebovanja: {trebovanje_stats[0]}")
        print(f"   Recent (24h): {trebovanje_stats[1]}")
        
        # 4. Check import jobs
        print("\n3. Checking import jobs...")
        result = await conn.execute(
            text("""
                SELECT status, COUNT(*) as count
                FROM import_job 
                GROUP BY status
                ORDER BY status
            """)
        )
        import_stats = result.fetchall()
        
        if import_stats:
            for status, count in import_stats:
                print(f"   {status}: {count}")
        else:
            print("   No import jobs found")
        
        # 5. Check magacin and radnja entries
        print("\n4. Checking locations...")
        result = await conn.execute(text("SELECT COUNT(*) FROM magacin"))
        magacin_count = result.fetchone()[0]
        
        result = await conn.execute(text("SELECT COUNT(*) FROM radnja"))
        radnja_count = result.fetchone()[0]
        
        print(f"   Magacini: {magacin_count}")
        print(f"   Radnje: {radnja_count}")
        
        print("\n✅ Import setup verification completed!")
        print("\n🔧 To test import:")
        print("   1. Upload an Excel file through the admin interface")
        print("   2. Check that it appears in trebovanje list")
        print("   3. Check that it appears in scheduler")
        
        return True
    
    await engine.dispose()

async def show_sample_trebovanje_query():
    """Show a sample query to check trebovanja"""
    print("\n📝 Sample SQL to check trebovanja:")
    print("""
    SELECT 
        t.dokument_broj,
        t.status,
        t.created_at,
        m.naziv as magacin,
        r.naziv as radnja,
        COUNT(ts.id) as stavke_count
    FROM trebovanje t
    LEFT JOIN magacin m ON t.magacin_id = m.id
    LEFT JOIN radnja r ON t.radnja_id = r.id
    LEFT JOIN trebovanje_stavka ts ON t.id = ts.trebovanje_id
    WHERE t.created_at > NOW() - INTERVAL '1 hour'
    GROUP BY t.id, m.naziv, r.naziv
    ORDER BY t.created_at DESC;
    """)

if __name__ == "__main__":
    async def main():
        success = await verify_import_setup()
        await show_sample_trebovanje_query()
        if not success:
            sys.exit(1)
    
    asyncio.run(main())
