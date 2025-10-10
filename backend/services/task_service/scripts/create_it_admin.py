import asyncio
import asyncpg
from datetime import datetime

async def create_admin_user():
    """Create admin user: it@cungu.com / Dekodera1989"""
    
    # Database connection (use Docker service name)
    conn = await asyncpg.connect(
        host="db",  # Docker service name
        port=5432,
        user="magacin_user",
        password="magacin_pass",
        database="magacin_db"
    )
    
    try:
        # Check if user already exists
        existing = await conn.fetchval(
            "SELECT id FROM users WHERE email = $1",
            "it@cungu.com"
        )
        
        if existing:
            print("❌ User it@cungu.com already exists!")
            return
        
        # Hash password using bcrypt
        import bcrypt
        password_hash = bcrypt.hashpw("Dekodera1989".encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert new admin user
        user_id = await conn.fetchval("""
            INSERT INTO users (
                email,
                password_hash,
                full_name,
                role,
                is_active,
                created_at,
                updated_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7)
            RETURNING id
        """,
            "it@cungu.com",
            password_hash,
            "IT Admin",
            "admin",  # role as lowercase string
            True,
            datetime.utcnow(),
            datetime.utcnow()
        )
        
        print(f"✅ Admin user created successfully!")
        print(f"   ID: {user_id}")
        print(f"   Email: it@cungu.com")
        print(f"   Password: Dekodera1989")
        print(f"   Role: ADMIN")
        
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(create_admin_user())

