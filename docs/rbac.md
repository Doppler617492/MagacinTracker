# RBAC (Role-Based Access Control) - Documentation

**Feature:** Sprint WMS Phase 2  
**Purpose:** Granular access control and task visibility  
**Language:** Serbian (Srpski)

---

## Overview

RBAC (Role-Based Access Control) provides fine-grained access control with visibility policies:

**5 Roles:**
1. **Admin** - Full system access (sve)
2. **Menadžer** - Manager - all locations, reports, analytics (globalni pristup)
3. **Šef** - Supervisor - location-based access (pristup po lokaciji)
4. **Komercijalista** - Sales - read-only, reports (samo čitanje)
5. **Magacioner** - Worker - own tasks + team tasks (samo moji i tim)

---

## Role Definitions

### 1. Admin (Administrator)

**Permissions:**
- ✅ Full CRUD on all entities
- ✅ User management (create, edit, delete)
- ✅ Role assignment
- ✅ Team management
- ✅ System settings
- ✅ All locations/warehouses
- ✅ All reports and analytics

**Visibility:**
- See ALL tasks globally
- See ALL receivings globally
- See ALL users

**Serbian Label:** "Administrator"

---

### 2. Menadžer (Manager)

**Permissions:**
- ✅ View all tasks (all locations)
- ✅ View all receivings
- ✅ Generate reports
- ✅ View analytics/KPI
- ✅ View all users (read-only)
- ❌ Cannot create/edit users
- ❌ Cannot change system settings

**Visibility:**
- See ALL tasks globally
- See ALL receivings globally
- See ALL users (read-only)

**Serbian Label:** "Menadžer"

---

### 3. Šef (Supervisor)

**Permissions:**
- ✅ View tasks in assigned location
- ✅ Assign tasks to workers
- ✅ View receivings in assigned location
- ✅ Generate location reports
- ✅ View location KPIs
- ❌ Cannot access other locations
- ❌ Cannot manage users

**Visibility:**
- See tasks where `trebovanje.magacin_id = šef.magacin_id`
- See receivings where `receiving.magacin_id = šef.magacin_id`
- See workers in same location

**Serbian Label:** "Šef"

---

### 4. Komercijalista (Sales)

**Permissions:**
- ✅ View tasks (read-only)
- ✅ View reports
- ✅ Export data (CSV)
- ❌ Cannot modify tasks
- ❌ Cannot assign tasks
- ❌ Cannot start/complete tasks

**Visibility:**
- See ALL tasks (read-only)
- See ALL receivings (read-only)
- Cannot see user management

**Serbian Label:** "Komercijalista"

---

### 5. Magacioner (Warehouse Worker)

**Permissions:**
- ✅ View own assigned tasks
- ✅ View team tasks (if in team)
- ✅ Start/complete tasks
- ✅ Receive items (prijem)
- ✅ Upload photos
- ❌ Cannot see other workers' tasks
- ❌ Cannot assign tasks
- ❌ Cannot access reports

**Visibility:**
- See tasks where `zaduznica.magacioner_id = current_user.id`
- See tasks where `zaduznica.team_id = current_user.team_id`
- Cannot see tasks assigned to other workers/teams

**Serbian Label:** "Magacioner"

---

## Visibility Policy Implementation

### Backend Middleware

```python
# File: backend/services/task_service/app/middleware/rbac.py

async def filter_tasks_by_role(
    user: UserAccount,
    query: Select
) -> Select:
    """
    Apply RBAC filtering to task queries
    
    Returns modified query with WHERE clauses
    """
    if user.role == Role.ADMIN or user.role == Role.MENADZER:
        # No filter - see all
        return query
    
    elif user.role == Role.SEF:
        # Filter by magacin
        user_magacin_id = await get_user_magacin(user.id)
        return query.join(Trebovanje).where(
            Trebovanje.magacin_id == user_magacin_id
        )
    
    elif user.role == Role.MAGACIONER:
        # Filter by assigned to me OR my team
        user_team_id = await get_user_team(user.id)
        return query.where(
            or_(
                Zaduznica.magacioner_id == user.id,
                Zaduznica.team_id == user_team_id
            )
        )
    
    elif user.role == Role.KOMERCIJALISTA:
        # Read-only, see all
        return query
    
    else:
        # Unknown role - deny all
        return query.where(False)
```

### Frontend Guard

```typescript
// File: frontend/admin/src/guards/RBACGuard.tsx

export const canAccessRoute = (user: User, route: string): boolean => {
  const role = user.role;
  
  // Admin can access everything
  if (role === 'admin') return true;
  
  // Menadžer can access most things except user management
  if (role === 'menadzer') {
    return !route.includes('/users');
  }
  
  // Šef can access operations and reports
  if (role === 'sef') {
    return ['/trebovanja', '/zaduznice', '/receiving', '/reports'].some(
      r => route.includes(r)
    );
  }
  
  // Komercijalista read-only
  if (role === 'komercijalista') {
    return ['/trebovanja', '/reports', '/analytics'].some(
      r => route.includes(r)
    );
  }
  
  // Magacioner should use PWA, not admin
  return false;
};
```

---

## API Authorization

### Endpoint Protection

```python
@router.get("/zaduznice")
async def list_zaduznice(
    current_user: UserAccount = Depends(get_current_user),
    db = Depends(get_db)
):
    """List zaduznice with RBAC filtering"""
    
    # Build base query
    query = select(Zaduznica)
    
    # Apply RBAC filter
    query = await filter_tasks_by_role(current_user, query)
    
    # Execute
    result = await db.execute(query)
    return result.scalars().all()
```

### 403 Forbidden Responses

```python
# If user tries to access unauthorized resource
if not can_access_resource(current_user, resource):
    raise HTTPException(
        status_code=403,
        detail="Nemate pristup ovom resursu"  # Serbian
    )
```

---

## Admin UI Implementation

### User Management Page

**File:** `frontend/admin/src/pages/UsersRolesPage.tsx`

```tsx
Table Columns:
- Ime i prezime
- Email
- Uloga (badge with color)
- Tim (if magacioner)
- Magacin (if šef)
- Aktivan (toggle)
- Akcije (Edit, Reset Password, Delete)

Actions:
- Create User: Opens modal
- Edit: Change role, assign team/location
- Reset Password: Admin-only action
- Deactivate: Soft delete
```

### Create/Edit User Modal

```tsx
<Modal title={isEdit ? "Izmijeni korisnika" : "Kreiraj korisnika"}>
  <Form layout="vertical">
    <Form.Item label="Ime" required>
      <Input />
    </Form.Item>
    
    <Form.Item label="Prezime" required>
      <Input />
    </Form.Item>
    
    <Form.Item label="Email" required>
      <Input type="email" />
    </Form.Item>
    
    <Form.Item label="Uloga" required>
      <Select>
        <Option value="admin">Administrator</Option>
        <Option value="menadzer">Menadžer</Option>
        <Option value="sef">Šef</Option>
        <Option value="komercijalista">Komercijalista</Option>
        <Option value="magacioner">Magacioner</Option>
      </Select>
    </Form.Item>
    
    {/* Conditional fields based on role */}
    {role === 'magacioner' && (
      <Form.Item label="Tim">
        <Select>
          <Option value="team-a1">Tim A1 (Smjena A)</Option>
          <Option value="team-b1">Tim B1 (Smjena B)</Option>
        </Select>
      </Form.Item>
    )}
    
    {role === 'sef' && (
      <Form.Item label="Magacin">
        <Select>
          <Option value="mag-1">Veleprodajni Magacin</Option>
        </Select>
      </Form.Item>
    )}
    
    {!isEdit && (
      <Form.Item label="Lozinka" required>
        <Input.Password />
      </Form.Item>
    )}
  </Form>
</Modal>
```

---

## Task Visibility Examples

### Example 1: Magacioner Visibility

**User:** Sabin Maku (magacioner, Tim A1)

**Sees:**
```sql
SELECT z.* 
FROM zaduznica z
WHERE z.magacioner_id = 'sabin-uuid'
   OR z.team_id = 'team-a1-uuid'
```

**Does NOT see:**
- Tasks assigned to other workers
- Tasks assigned to other teams
- Unassigned tasks

---

### Example 2: Šef Visibility

**User:** Manager (šef, Magacin 1)

**Sees:**
```sql
SELECT z.*
FROM zaduznica z
JOIN trebovanje t ON z.trebovanje_id = t.id
WHERE t.magacin_id = 'magacin-1-uuid'
```

**Does NOT see:**
- Tasks in other warehouses

---

### Example 3: Admin/Menadžer Visibility

**Sees:** Everything (no WHERE clause restrictions)

---

## PWA Header RBAC Display

```tsx
<ManhattanHeader
  user={{
    firstName: "Sabin",
    lastName: "Maku",
    role: "Magacioner"  // Serbian label
  }}
  team={{
    name: "Tim A1",
    shift: "A"
  }}
/>

// Header shows:
// [SM] Sabin Maku     │ Smjena A      │ ● Online
//      Magacioner     │ 08:00-15:00   │   Odjava
```

---

## Seed Data

### Create Test Users

```python
# File: backend/services/task_service/scripts/seed_users_rbac.py

users = [
    {
        "email": "admin@magacin.com",
        "password": "admin123",
        "first_name": "Admin",
        "last_name": "User",
        "role": "ADMIN"
    },
    {
        "email": "menadzer@magacin.com",
        "password": "menadzer123",
        "first_name": "Menadžer",
        "last_name": "Glavni",
        "role": "MENADZER"
    },
    {
        "email": "sef.magacin1@cungu.com",
        "password": "sef123",
        "first_name": "Šef",
        "last_name": "Magacin 1",
        "role": "SEF",
        "magacin_id": "magacin-1-uuid"
    },
    {
        "email": "komercijalista@cungu.com",
        "password": "kom123",
        "first_name": "Komercijalista",
        "last_name": "Prodaja",
        "role": "KOMERCIJALISTA"
    },
    {
        "email": "sabin.maku@cungu.com",
        "password": "test123",
        "first_name": "Sabin",
        "last_name": "Maku",
        "role": "MAGACIONER",
        "team_id": "team-a1-uuid"
    }
]
```

---

## Testing RBAC

### Test Case: Magacioner Cannot See Other Tasks

```python
async def test_magacioner_visibility():
    # Login as Sabin (magacioner, Team A1)
    token_sabin = await login("sabin.maku@cungu.com", "test123")
    
    # Get tasks
    response = await client.get(
        "/api/zaduznice",
        headers={"Authorization": f"Bearer {token_sabin}"}
    )
    
    tasks = response.json()
    
    # Verify only own/team tasks visible
    for task in tasks:
        assert (
            task['magacioner_id'] == sabin_user_id or
            task['team_id'] == 'team-a1-uuid'
        )
```

### Test Case: 403 When Accessing Unauthorized

```python
async def test_forbidden_access():
    # Login as magacioner
    token = await login("sabin.maku@cungu.com", "test123")
    
    # Try to access admin endpoint
    response = await client.get(
        "/api/users",
        headers={"Authorization": f"Bearer {token}"}
    )
    
    # Should return 403
    assert response.status_code == 403
    assert "Nemate pristup" in response.json()['detail']
```

---

## UI Visibility

### Admin Navigation by Role

```typescript
const getVisibleMenuItems = (role: string) => {
  const allItems = {
    operacije: ['trebovanja', 'zaduznice', 'receiving', 'import'],
    katalog: ['artikli', 'barkodovi'],
    analitika: ['kpi', 'reports', 'ai'],
    uzivo: ['tv', 'live-ops'],
    admin: ['users', 'settings']
  };
  
  switch (role) {
    case 'admin':
      return allItems;  // All sections
    
    case 'menadzer':
      return { ...allItems, admin: [] };  // No user management
    
    case 'sef':
      return { 
        operacije: allItems.operacije,
        analitika: ['reports']  // Limited analytics
      };
    
    case 'komercijalista':
      return {
        operacije: ['trebovanja'],  // Read-only
        analitika: ['reports']
      };
    
    default:
      return {};  // Magacioner uses PWA, not admin
  }
};
```

---

## Password Reset

### Admin Reset User Password

```python
@router.post("/users/{user_id}/reset-password")
async def reset_password(
    user_id: UUID,
    new_password: str,
    current_user: UserAccount = Depends(require_admin)
):
    """
    Reset user password (admin only)
    Serbian: Resetuj lozinku
    """
    # Only admin can reset passwords
    if current_user.role != Role.ADMIN:
        raise HTTPException(403, "Samo administrator može resetovati lozinke")
    
    # Hash new password
    hashed = hash_password(new_password)
    
    # Update user
    await db.execute(
        update(UserAccount)
        .where(UserAccount.id == user_id)
        .values(hashed_password=hashed)
    )
    
    # Audit log
    await record_audit(
        action=AuditAction.PASSWORD_RESET,
        actor_id=current_user.id,
        entity_type="user",
        entity_id=str(user_id)
    )
    
    return {"message": "Lozinka resetovana uspješno"}
```

---

## Audit Trail

**RBAC-Related Audit Events:**
```python
AuditAction.USER_CREATED
AuditAction.USER_ROLE_CHANGED
AuditAction.USER_DEACTIVATED
AuditAction.PASSWORD_RESET
AuditAction.TEAM_ASSIGNED
AuditAction.LOCATION_ASSIGNED
```

**Query Audit Log:**
```sql
SELECT 
    a.action,
    u.first_name || ' ' || u.last_name as actor,
    a.entity_type,
    a.details,
    a.timestamp
FROM audit_log a
JOIN users u ON a.user_id = u.id
WHERE a.action IN ('USER_CREATED', 'USER_ROLE_CHANGED', 'PASSWORD_RESET')
ORDER BY a.timestamp DESC
LIMIT 50;
```

---

## Serbian UI Labels

```typescript
export const rbacLabels = {
  roles: {
    admin: "Administrator",
    menadzer: "Menadžer",
    sef: "Šef",
    komercijalista: "Komercijalista",
    magacioner: "Magacioner"
  },
  
  permissions: {
    full: "Potpun pristup",
    limited: "Ograničen pristup",
    readonly: "Samo čitanje",
    own: "Samo svoje",
    team: "Zadaci tima",
    location: "Zadaci lokacije"
  },
  
  actions: {
    assignRole: "Dodijeli ulogu",
    assignTeam: "Dodijeli tim",
    resetPassword: "Resetuj lozinku",
    deactivate: "Deaktiviraj",
    activate: "Aktiviraj"
  },
  
  messages: {
    accessDenied: "Nemate pristup ovom resursu",
    roleChanged: "Uloga uspješno promijenjena",
    passwordReset: "Lozinka resetovana",
    userCreated: "Korisnik kreiran",
    userDeactivated: "Korisnik deaktiviran"
  }
};
```

---

## Testing

### Test Scenario 1: Magacioner Access

```bash
# Login as Sabin (magacioner)
TOKEN=$(curl -s -X POST http://localhost:8123/api/auth/login \
  -d '{"username":"sabin.maku@cungu.com","password":"test123"}' \
  | jq -r '.access_token')

# Get tasks - should only see own/team
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8123/api/zaduznice | jq '. | length'

# Expected: Only tasks assigned to Sabin or Team A1

# Try to access admin endpoint - should fail
curl -H "Authorization: Bearer $TOKEN" \
  http://localhost:8123/api/users

# Expected: 403 Forbidden
# {"detail": "Nemate pristup ovom resursu"}
```

---

## Best Practices

### 1. Least Privilege Principle
- Assign minimum role needed
- Use magacioner for warehouse workers
- Reserve admin for IT/system admins only

### 2. Team-Based Access
- Always assign magacioneri to teams
- Teams enable collaborative work
- Teams enable load balancing

### 3. Location-Based Segregation
- Assign šef to specific warehouse
- Prevents cross-location data leakage
- Supports multi-warehouse deployments

### 4. Audit Everything
- Log all role changes
- Log all password resets
- Log all permission grants
- Retention: 1 year minimum

---

**Document Version:** 1.0  
**Last Updated:** October 19, 2025  
**Status:** ✅ Documented


