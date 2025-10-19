#!/usr/bin/env python3
"""
Create the service user needed for import service authentication.
Run with: python scripts/create_service_user.py
"""

import asyncio
import sys
from pathlib import Path
import uuid
from datetime import datetime, timezone

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app_common.config import get_settings
from app_common.security import get_password_hash

settings = get_settings()

# Service user configuration (matches import service config)
SERVICE_USER = {
    "id": "00000000-0000-0000-0000-000000000001",
    "email": "import.service@magacin.com",
    "password": "ServiceUser123!",
    "first_name": "Import",
    "last_name": "Service",
    "role": "komercijalista",
    "is_active": True
}

async def create_service_user():
    """Create the service user needed for import authentication"""
    # Create async engine
    engine = create_async_engine(settings.database_url)
    
    print("🔧 Creating service user for import authentication...")
    
    async with engine.begin() as conn:
        # Check if service user already exists
        result = await conn.execute(
            text("SELECT id FROM users WHERE id = :id OR email = :email"),
            {"id": SERVICE_USER["id"], "email": SERVICE_USER["email"]}
        )
        existing_user = result.fetchone()
        
        if existing_user:
            print(f"✅ Service user already exists (ID: {existing_user[0]})")
            return
        
        try:
            # Hash password
            password_hash = get_password_hash(SERVICE_USER["password"])
            
            # Insert service user
            await conn.execute(
                text("""
                    INSERT INTO users (id, email, password_hash, first_name, last_name, role, is_active, created_at, updated_at)
                    VALUES (:id, :email, :password_hash, :first_name, :last_name, :role, :is_active, :created_at, :updated_at)
                """),
                {
                    "id": SERVICE_USER["id"],
                    "email": SERVICE_USER["email"],
                    "password_hash": password_hash,
                    "first_name": SERVICE_USER["first_name"],
                    "last_name": SERVICE_USER["last_name"],
                    "role": SERVICE_USER["role"],
                    "is_active": SERVICE_USER["is_active"],
                    "created_at": datetime.now(timezone.utc),
                    "updated_at": datetime.now(timezone.utc)
                }
            )
            
            print(f"✅ Service user created successfully!")
            print(f"   ID: {SERVICE_USER['id']}")
            print(f"   Email: {SERVICE_USER['email']}")
            print(f"   Role: {SERVICE_USER['role']}")
            print(f"   This user will be used by the import service for authentication")
            
        except Exception as e:
            print(f"❌ Failed to create service user: {e}")
            raise
    
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(create_service_user())
