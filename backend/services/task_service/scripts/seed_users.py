#!/usr/bin/env python3
"""
Seed script for initial users in the Magacin Track system.
Run with: python scripts/seed_users.py
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session

from app_common.db import get_db
from app_common.security import get_password_hash
from app.models.enums import Role
from app.models.user import UserAccount
from app.services.user_service import UserService


# Initial users to create
USERS = [
    {
        "email": "admin@magacin.com",
        "password": "Admin123!",
        "first_name": "System",
        "last_name": "Administrator",
        "role": Role.ADMIN,
        "is_active": True
    },
    {
        "email": "marko.sef@magacin.com",
        "password": "Magacin123!",
        "first_name": "Marko",
        "last_name": "Šef",
        "role": Role.SEF,
        "is_active": True
    },
    {
        "email": "jana.komercijalista@magacin.com",
        "password": "Magacin123!",
        "first_name": "Jana",
        "last_name": "Komercijalista",
        "role": Role.KOMERCIJALISTA,
        "is_active": True
    },
    {
        "email": "luka.magacioner@magacin.com",
        "password": "Magacin123!",
        "first_name": "Luka",
        "last_name": "Magacioner",
        "role": Role.MAGACIONER,
        "is_active": True
    },
    {
        "email": "ivana.menadzer@magacin.com",
        "password": "Magacin123!",
        "first_name": "Ivana",
        "last_name": "Menadžer",
        "role": Role.MENADZER,
        "is_active": True
    },
]


async def seed_users():
    """Seed initial users into the database"""
    async for db in get_db():
        user_service = UserService(db)
        break
    
    print("🌱 Seeding initial users...")
    
    # Find admin user to use as creator for other users
    admin_user = user_service.get_user_by_email("admin@magacin.com")
    if not admin_user:
        print("❌ Admin user not found. Please create admin user first.")
        return
    
    created_count = 0
    skipped_count = 0
    
    for user_data in USERS:
        # Check if user already exists
        existing_user = user_service.get_user_by_email(user_data["email"])
        if existing_user:
            print(f"⏭️  User {user_data['email']} already exists, skipping...")
            skipped_count += 1
            continue
        
        try:
            # Create user using the service
            from app.schemas.user import UserCreate
            user_create = UserCreate(**user_data)
            user = user_service.create_user(user_create, admin_user.id)
            
            print(f"✅ Created user: {user.email} ({user.role.value})")
            created_count += 1
            
        except Exception as e:
            print(f"❌ Failed to create user {user_data['email']}: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Created: {created_count} users")
    print(f"   Skipped: {skipped_count} users")
    print(f"   Total: {len(USERS)} users")
    
    # Show all users
    print(f"\n👥 All users in system:")
    users, total = user_service.list_users(per_page=100)
    for user in users:
        status = "🟢" if user.is_active else "🔴"
        print(f"   {status} {user.email} ({user.role.value}) - {user.full_name}")


if __name__ == "__main__":
    import asyncio
    asyncio.run(seed_users())
