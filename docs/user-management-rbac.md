# User Management & RBAC System

## Overview

The Magacin Track platform now includes a comprehensive User Management & Role-Based Access Control (RBAC) system that provides secure authentication, authorization, and user administration capabilities across all components.

## Architecture

### Components

1. **Task Service** - Central user management and authentication
2. **API Gateway** - JWT validation and RBAC middleware
3. **Admin Interface** - User management UI
4. **PWA** - Worker authentication and task access
5. **TV Dashboard** - Read-only access with API token

### Database Schema

#### Users Table
```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    role user_role_enum NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    last_login TIMESTAMP WITH TIME ZONE,
    created_by UUID REFERENCES users(id)
);
```

#### Audit Log Table
```sql
CREATE TABLE audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID REFERENCES users(id),
    action audit_action NOT NULL,
    entity_type VARCHAR(64),
    entity_id VARCHAR(64),
    payload JSONB NOT NULL DEFAULT '{}',
    ip_address VARCHAR(45),
    user_agent VARCHAR(500),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);
```

## Roles and Permissions

### Role Hierarchy

1. **ADMIN** - Full system access
   - User management (CRUD)
   - System configuration
   - All API endpoints
   - Audit logs access

2. **MENADZER** - Management access
   - KPI and analytics (read-only)
   - Reports and exports
   - TV dashboard access
   - Monitoring data

3. **SEF** - Supervisor access
   - Task assignment and reassignment
   - Zadužnice management
   - Scheduler operations
   - Worker performance monitoring

4. **KOMERCIJALISTA** - Commercial access
   - Import operations
   - Trebovanja creation
   - File uploads (CSV/XLSX)
   - Order management

5. **MAGACIONER** - Worker access
   - Personal task list
   - Task execution
   - Scanning operations
   - Manual completion

### API Endpoint Access

| Endpoint | ADMIN | MENADZER | SEF | KOMERCIJALISTA | MAGACIONER |
|----------|-------|----------|-----|----------------|------------|
| `/api/admin/users/*` | ✅ | ❌ | ❌ | ❌ | ❌ |
| `/api/kpi/*` | ✅ | ✅ (R) | ✅ | ❌ | ❌ |
| `/api/reports/*` | ✅ | ✅ (R) | ❌ | ❌ | ❌ |
| `/api/tv/*` | ✅ | ✅ (R) | ✅ | ❌ | ❌ |
| `/api/zaduznice/*` | ✅ | ❌ | ✅ | ❌ | ❌ |
| `/api/scheduler/*` | ✅ | ❌ | ✅ | ❌ | ❌ |
| `/api/import/*` | ✅ | ❌ | ✅ | ✅ | ❌ |
| `/api/trebovanja/*` | ✅ | ❌ | ❌ | ✅ | ❌ |
| `/api/worker/tasks/*` | ✅ | ❌ | ❌ | ❌ | ✅ (own) |

Legend: ✅ = Full access, ✅ (R) = Read-only, ❌ = No access, ✅ (own) = Own data only

## Authentication Flow

### JWT Token Structure
```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "MAGACIONER",
  "exp": 1738947600
}
```

### Login Process
1. User submits credentials to `/api/auth/login`
2. System validates credentials against database
3. JWT token generated with 8-hour expiration
4. Token stored in secure cookie or localStorage
5. Audit log entry created for successful/failed login

### Token Validation
1. API Gateway intercepts requests
2. JWT token extracted from Authorization header
3. Token signature and expiration validated
4. User role extracted for RBAC checks
5. Request forwarded to appropriate service

## Security Features

### Password Policy
- Minimum 8 characters
- At least 1 uppercase letter
- At least 1 number
- At least 1 special character
- bcrypt hashing with cost factor ≥ 12

### Session Management
- JWT tokens valid for 8 hours
- Refresh token rotation (7 days)
- Secure token storage
- Automatic token cleanup on logout

### Audit Logging
All authentication and user management actions are logged:
- `LOGIN_SUCCESS` - Successful login
- `LOGIN_FAILED` - Failed login attempt
- `LOGOUT` - User logout
- `PASSWORD_RESET` - Password reset
- `USER_CREATED` - New user creation
- `USER_ROLE_CHANGED` - Role modification
- `USER_DEACTIVATED` - User deactivation

### Security Monitoring
- Failed login attempt tracking
- IP address logging
- User agent tracking
- Suspicious activity detection

## API Endpoints

### Authentication
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout
- `GET /api/auth/profile` - Current user profile
- `POST /api/auth/reset-request` - Password reset request
- `POST /api/auth/reset-password` - Password reset confirmation

### User Management (ADMIN only)
- `GET /api/admin/users` - List users with pagination/filters
- `POST /api/admin/users` - Create new user
- `GET /api/admin/users/{id}` - Get user details
- `PATCH /api/admin/users/{id}` - Update user
- `DELETE /api/admin/users/{id}` - Deactivate user
- `POST /api/admin/users/{id}/reset-password` - Reset user password
- `GET /api/admin/users/stats` - User statistics

### Metrics (ADMIN only)
- `GET /api/metrics/auth` - Authentication metrics
- `GET /api/metrics/user-activity` - User activity metrics
- `GET /api/metrics/security` - Security metrics
- `GET /api/metrics/all` - All metrics combined

## Frontend Integration

### Admin Interface
- User management dashboard
- Role assignment interface
- User activity monitoring
- CSV export functionality
- Real-time user statistics

### PWA (Worker Interface)
- Secure login page
- JWT token storage in IndexedDB
- Offline token caching (24h)
- Automatic token refresh
- Role-based task filtering

### TV Dashboard
- API token authentication
- Read-only access
- No user-specific data
- Public monitoring display

## Deployment

### Database Migration
```bash
# Run the user management migration
docker compose exec task-service alembic upgrade head
```

### Seed Initial Users
```bash
# Create initial admin and test users
docker compose exec task-service python scripts/seed_users.py
```

### Environment Variables
```env
# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=480  # 8 hours

# Database
DATABASE_URL=postgresql://user:pass@localhost/magacin

# CORS
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]
CORS_ALLOW_CREDENTIALS=true
```

## Monitoring and Metrics

### Prometheus Metrics
- `auth_login_success_total` - Successful logins
- `auth_login_failed_total` - Failed login attempts
- `active_users_total` - Currently active users
- `role_distribution_total` - Users per role

### Grafana Dashboards
- Authentication success/failure rates
- User activity patterns
- Role distribution charts
- Security incident tracking

## Testing

### Test Users
The seed script creates these test users:
- `admin@magacin.com` / `Admin123!` (ADMIN)
- `marko.sef@magacin.com` / `Magacin123!` (SEF)
- `jana.komercijalista@magacin.com` / `Magacin123!` (KOMERCIJALISTA)
- `luka.magacioner@magacin.com` / `Magacin123!` (MAGACIONER)
- `ivana.menadzer@magacin.com` / `Magacin123!` (MENADZER)

### API Testing
```bash
# Login as admin
curl -X POST http://localhost:8123/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin@magacin.com", "password": "Admin123!"}'

# List users (requires admin token)
curl -X GET http://localhost:8123/api/admin/users \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

## Security Considerations

### Production Checklist
- [ ] Strong JWT secret key (256-bit)
- [ ] HTTPS enforcement
- [ ] Rate limiting on auth endpoints
- [ ] IP whitelisting for admin access
- [ ] Regular security audits
- [ ] Password policy enforcement
- [ ] Session timeout configuration
- [ ] Audit log retention policy

### Future Enhancements
- Two-factor authentication (2FA)
- Single Sign-On (SSO) integration
- API key management
- Advanced threat detection
- User activity analytics
- Automated security alerts

## Troubleshooting

### Common Issues

1. **Login fails with 401**
   - Check user credentials
   - Verify user is active
   - Check password policy compliance

2. **403 Forbidden on API calls**
   - Verify JWT token is valid
   - Check user role permissions
   - Ensure token hasn't expired

3. **Database connection errors**
   - Verify DATABASE_URL configuration
   - Check database server status
   - Run pending migrations

4. **CORS errors in frontend**
   - Update CORS_ORIGINS configuration
   - Check API Gateway CORS settings
   - Verify frontend URL matches allowed origins

### Logs and Debugging
```bash
# View authentication logs
docker compose logs task-service | grep -i auth

# Check user creation
docker compose logs task-service | grep -i "user created"

# Monitor failed logins
docker compose logs task-service | grep -i "login failed"
```

## Support

For issues or questions regarding the User Management & RBAC system:
1. Check the troubleshooting section above
2. Review audit logs for authentication events
3. Verify role permissions and API endpoint access
4. Contact the development team for advanced configuration

---

*Last updated: December 2024*
*Version: 1.0.0*
