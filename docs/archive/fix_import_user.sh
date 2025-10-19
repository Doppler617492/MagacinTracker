#!/bin/bash

echo "🔧 Fix Import User Script"
echo "========================="
echo ""

# Check if Docker is running
if ! docker info >/dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    echo ""
    echo "Manual options:"
    echo "1. Start your database manually"
    echo "2. Run the SQL script: create_service_user.sql"
    echo "3. Or use any of the Python scripts when database is accessible"
    exit 1
fi

echo "✅ Docker is running"

# Check if magacin containers are running
if docker-compose ps | grep -q "magacin"; then
    echo "✅ Magacin Track containers are running"
    
    # Try to create service user via database
    echo ""
    echo "🚀 Creating service user in database..."
    
    docker-compose exec -T db psql -U magacin_user -d magacin_db << 'EOF'
-- Create service user for import authentication
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM users WHERE id = '00000000-0000-0000-0000-000000000001' OR email = 'import.service@magacin.com') THEN
    RAISE NOTICE '✅ Service user already exists';
  ELSE
    INSERT INTO users (
      id, 
      email, 
      password_hash, 
      first_name, 
      last_name, 
      role, 
      is_active, 
      created_at, 
      updated_at
    ) VALUES (
      '00000000-0000-0000-0000-000000000001',
      'import.service@magacin.com',
      '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewkGm0JfJGfhqHnK',
      'Import',
      'Service',
      'komercijalista',
      true,
      NOW(),
      NOW()
    );
    
    RAISE NOTICE '✅ Service user created successfully!';
  END IF;
END $$;

-- Verify user exists
SELECT 
  'Service User Details:' as info,
  id,
  email, 
  role,
  is_active
FROM users 
WHERE id = '00000000-0000-0000-0000-000000000001';
EOF

    echo ""
    echo "🎉 Service user setup complete!"
    echo ""
    echo "✅ What this fixed:"
    echo "   - Created service user (ID: 00000000-0000-0000-0000-000000000001)"
    echo "   - Role: komercijalista (required for import authentication)"
    echo "   - Email: import.service@magacin.com"
    echo ""
    echo "🧪 Test your import:"
    echo "   1. Go to the admin interface"  
    echo "   2. Upload an Excel file in 'Import' section"
    echo "   3. Check that it shows 'done'"
    echo "   4. Verify trebovanje appears in 'Trebovanja' list"
    echo "   5. Verify trebovanje appears in 'Scheduler'"
    
else
    echo "❌ Magacin Track containers are not running"
    echo ""
    echo "To start the system:"
    echo "   docker-compose up -d"
    echo ""
    echo "Then run this script again, or manually:"
    echo "   1. Use: create_service_user.sql (SQL script)"
    echo "   2. Or: backend/services/task_service/scripts/create_service_user_asyncpg.py"
fi

echo ""
echo "📋 Additional help:"
echo "   - SQL script: create_service_user.sql"
echo "   - Documentation: fix-import-issue.md"
echo "   - Verification: backend/services/task_service/scripts/verify_import_setup.py"
