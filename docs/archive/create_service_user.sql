-- SQL script to create the service user needed for Excel import functionality
-- Run this script against your magacin_db database

-- Check if service user already exists
DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM users WHERE id = '00000000-0000-0000-0000-000000000001' OR email = 'import.service@magacin.com') THEN
    RAISE NOTICE 'Service user already exists, skipping creation';
  ELSE
    -- Create service user for import authentication
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
      '$2b$12$YourHashedPasswordHere',  -- Will be updated below
      'Import',
      'Service',
      'komercijalista',
      true,
      NOW(),
      NOW()
    );
    
    RAISE NOTICE 'Service user created successfully!';
    RAISE NOTICE 'ID: 00000000-0000-0000-0000-000000000001';  
    RAISE NOTICE 'Email: import.service@magacin.com';
    RAISE NOTICE 'Role: komercijalista';
  END IF;
END $$;

-- Update password to a known hash for 'ServiceUser123!'
-- This bcrypt hash represents the password 'ServiceUser123!'
UPDATE users 
SET password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/lewkGm0JfJGfhqHnK'
WHERE id = '00000000-0000-0000-0000-000000000001';

-- Verify the user was created
SELECT 
  id,
  email, 
  first_name,
  last_name,
  role,
  is_active,
  created_at
FROM users 
WHERE id = '00000000-0000-0000-0000-000000000001';

-- Show summary
SELECT 
  'Service user setup complete!' as message,
  'Excel imports should now work correctly' as next_step;
