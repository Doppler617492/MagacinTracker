#!/usr/bin/env python3
"""
Simple script to create service user using asyncpg.
Run with: python3 scripts/create_service_user_asyncpg.py
"""

import asyncio
import os
import sys
import asyncpg
import bcrypt
from datetime import datetime

# Database connection details
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_USER = os.getenv("DB_USER", "magacin_user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "magacin_pass")
DB_NAME = os.getenv("DB_NAME", "magacin_db")

# Service user configuration
SERVICE_USER = {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "import.service@magacin.com",
    "first_name": "Import", 
    "last_name": "Service",
    "role": "komercijalista",
    "is_active": True
}

def get_password_hash(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

async def create_service_user():
    """Create the service user needed for import authentication"""
    
    try:
        # Connect to database
        conn = await asyncpg.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER, 
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        print("🔧 Creating service user for import authentication...")
        
        # Check if service user already exists
        existing_user = await conn.fetchrow(
            "SELECT id, email, role FROM users WHERE id = $1 OR email = $2",
            SERVICE_USER["id"], SERVICE_USER["email"]
        )
        
        if existing_user:
            print(f"✅ Service user already exists:")
            print(f"   ID: {existing_user['id']}")
            print(f"   Email: {existing_user['email']}")
            print(f"   Role: {existing_user['role']}")
            return True
        
        # Hash password
        password_hash = get_password_hash("ServiceUser123!")
        
        # Insert service user
        await conn.execute("""
            INSERT INTO users (id, email, password_hash, first_name, last_name, role, is_active, created_at, updated_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
        """,
            SERVICE_USER["id"],
            SERVICE_USER["email"],
            password_hash,
            SERVICE_USER["first_name"],
            SERVICE_USER["last_name"],
            SERVICE_USER["role"], 
            SERVICE_USER["is_active"],
            datetime.now(),
            datetime.now()
        )
        
        print(f"✅ Service user created successfully!")
        print(f"   ID: {SERVICE_USER['id']}")
        print(f"   Email: {SERVICE_USER['email']}")
        print(f"   Role: {SERVICE_USER['role']}")
        print(f"   This user will be used by the import service for authentication")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create service user: {e}")
        print(f"   Make sure the database is running and accessible")
        print(f"   Database: {DB_HOST}:{DB_PORT}/{DB_NAME}")
        return False
        
    finally:
        if 'conn' in locals():
            await conn.close()

async def main():
    """Main function"""
    success = await create_service_user()
    if not success:
        sys.exit(1)
    
    print("\n🎉 Service user setup complete!")
    print("   You can now test Excel import functionality.")
    print("   Imported trebovanja should appear in both trebovanje list and scheduler.")

if __name__ == "__main__":
    asyncio.run(main())
