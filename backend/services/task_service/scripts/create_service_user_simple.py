#!/usr/bin/env python3
"""
Simple script to create service user using direct SQL.
Run with: python3 scripts/create_service_user_simple.py
"""

import os
import sys
import psycopg2
from datetime import datetime

# Database connection details (from environment or defaults)
DB_HOST = os.getenv("DB_HOST", "localhost") 
DB_PORT = os.getenv("DB_PORT", "5432")
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
    """Simple bcrypt password hashing"""
    import bcrypt
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_service_user():
    """Create the service user needed for import authentication"""
    
    try:
        # Connect to database
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT, 
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )
        
        cur = conn.cursor()
        
        print("🔧 Creating service user for import authentication...")
        
        # Check if service user already exists
        cur.execute(
            "SELECT id, email, role FROM users WHERE id = %s OR email = %s",
            (SERVICE_USER["id"], SERVICE_USER["email"])
        )
        existing_user = cur.fetchone()
        
        if existing_user:
            print(f"✅ Service user already exists:")
            print(f"   ID: {existing_user[0]}")
            print(f"   Email: {existing_user[1]}")
            print(f"   Role: {existing_user[2]}")
            return True
        
        # Hash password
        password_hash = get_password_hash("ServiceUser123!")
        
        # Insert service user
        cur.execute("""
            INSERT INTO users (id, email, password_hash, first_name, last_name, role, is_active, created_at, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            SERVICE_USER["id"],
            SERVICE_USER["email"], 
            password_hash,
            SERVICE_USER["first_name"],
            SERVICE_USER["last_name"],
            SERVICE_USER["role"],
            SERVICE_USER["is_active"],
            datetime.now(),
            datetime.now()
        ))
        
        conn.commit()
        
        print(f"✅ Service user created successfully!")
        print(f"   ID: {SERVICE_USER['id']}")
        print(f"   Email: {SERVICE_USER['email']}")
        print(f"   Role: {SERVICE_USER['role']}")
        print(f"   This user will be used by the import service for authentication")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create service user: {e}")
        return False
        
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    success = create_service_user()
    if not success:
        sys.exit(1)
    
    print("\n🎉 Service user setup complete!")
    print("   You can now test Excel import functionality.")
    print("   Imported trebovanja should appear in both trebovanje list and scheduler.")
