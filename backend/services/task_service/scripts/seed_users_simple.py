#!/usr/bin/env python3
"""
Simple seed script for initial users in the Magacin Track system.
Run with: python scripts/seed_users_simple.py
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app_common.config import get_settings
from app_common.security import get_password_hash

settings = get_settings()

# Initial users to create
USERS = [
    {
        "email": "admin@magacin.com",
        "password": "Admin123!",
        "first_name": "System",
        "last_name": "Administrator",
        "role": "menadzer",  # Using existing enum value
        "is_active": True
    },
    {
        "email": "marko.sef@magacin.com",
        "password": "Magacin123!",
        "first_name": "Marko",
        "last_name": "Šef",
        "role": "sef",
        "is_active": True
    },
    {
        "email": "jana.komercijalista@magacin.com",
        "password": "Magacin123!",
        "first_name": "Jana",
        "last_name": "Komercijalista",
        "role": "komercijalista",
        "is_active": True
    },
    {
        "email": "luka.magacioner@magacin.com",
        "password": "Magacin123!",
        "first_name": "Luka",
        "last_name": "Magacioner",
        "role": "magacioner",
        "is_active": True
    },
    {
        "email": "ivana.menadzer@magacin.com",
        "password": "Magacin123!",
        "first_name": "Ivana",
        "last_name": "Menadžer",
        "role": "menadzer",
        "is_active": True
    },
]


async def seed_users():
    """Seed initial users into the database"""
    # Create async engine
    engine = create_async_engine(settings.database_url)
    
    print("🌱 Seeding initial users...")
    
    created_count = 0
    skipped_count = 0
    
    async with engine.begin() as conn:
        for user_data in USERS:
            # Check if user already exists
            result = await conn.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": user_data["email"]}
            )
            existing_user = result.fetchone()
            
            if existing_user:
                print(f"⏭️  User {user_data['email']} already exists, skipping...")
                skipped_count += 1
                continue
            
            try:
                # Hash password
                password_hash = get_password_hash(user_data["password"])
                
                # Insert user
                await conn.execute(
                    text("""
                        INSERT INTO users (email, password_hash, first_name, last_name, role, is_active)
                        VALUES (:email, :password_hash, :first_name, :last_name, :role, :is_active)
                    """),
                    {
                        "email": user_data["email"].lower(),
                        "password_hash": password_hash,
                        "first_name": user_data["first_name"],
                        "last_name": user_data["last_name"],
                        "role": user_data["role"],
                        "is_active": user_data["is_active"]
                    }
                )
                
                print(f"✅ Created user: {user_data['email']} ({user_data['role']})")
                created_count += 1
                
            except Exception as e:
                print(f"❌ Failed to create user {user_data['email']}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count} users")
    print(f"   Skipped: {skipped_count} users")
    print(f"   Total: {len(USERS)} users")
    
    # Show all users
    print(f"\n👥 All users in system:")
    async with engine.begin() as conn:
        result = await conn.execute(
            text("SELECT email, first_name, last_name, role, is_active FROM users ORDER BY email")
        )
        users = result.fetchall()
        
        for user in users:
            status = "🟢" if user.is_active else "🔴"
            full_name = f"{user.first_name} {user.last_name}"
            print(f"   {status} {user.email} ({user.role}) - {full_name}")
    
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(seed_users())
