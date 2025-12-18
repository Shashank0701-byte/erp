# RBAC (Role-Based Access Control) Implementation Guide

## Overview

This ERP system implements a comprehensive Role-Based Access Control (RBAC) system with client-side routing and protected routes based on user roles and permissions.

## Features

✅ **Role-Based Authentication** - Different user roles with specific permissions  
✅ **Protected Routes** - Automatic route protection based on roles and permissions  
✅ **Permission Checks** - Fine-grained permission control for actions  
✅ **Client-Side Routing** - Seamless navigation with Next.js App Router  
✅ **Unauthorized Handling** - Graceful handling of unauthorized access attempts  
✅ **Auto-Redirect** - Automatic redirection based on user roles after login  

## User Roles

The system supports the following roles:

| Role | Description | Access Level |
|------|-------------|--------------|
| **ADMIN** | System Administrator | Full access to all modules |
| **MANAGER** | Department Manager | Access to multiple modules with reporting |
| **FINANCE** | Finance Department | Full access to finance module |
| **INVENTORY** | Inventory Department | Full access to inventory module |
| **HR** | Human Resources | Full access to HR module |
| **SALES** | Sales Department | Full access to sales module |
| **VIEWER** | Read-Only User | View-only access to all modules |

## Permissions

Permissions are grouped by module:

### Finance Permissions
- `VIEW_FINANCE` - View financial data
- `CREATE_FINANCE` - Create financial entries
- `EDIT_FINANCE` - Edit financial entries
- `DELETE_FINANCE` - Delete financial entries
- `APPROVE_FINANCE` - Approve financial transactions

### Inventory Permissions
- `VIEW_INVENTORY` - View inventory data
- `CREATE_INVENTORY` - Create inventory items
- `EDIT_INVENTORY` - Edit inventory items
- `DELETE_INVENTORY` - Delete inventory items

### HR Permissions
- `VIEW_HR` - View HR data
- `CREATE_HR` - Create HR records
- `EDIT_HR` - Edit HR records
- `DELETE_HR` - Delete HR records

### Sales Permissions
- `VIEW_SALES` - View sales data
- `CREATE_SALES` - Create sales records
- `EDIT_SALES` - Edit sales records
- `DELETE_SALES` - Delete sales records

### Admin Permissions
- `MANAGE_USERS` - Manage user accounts
- `MANAGE_ROLES` - Manage roles and permissions
- `VIEW_REPORTS` - Access system reports
- `SYSTEM_SETTINGS` - Configure system settings

## Usage

### 1. Protecting Pages with ProtectedRoute

Wrap your page component with `ProtectedRoute` to enforce authentication and authorization:

```tsx
import { ProtectedRoute } from '@/lib/auth/ProtectedRoute';
import { UserRole, Permission } from '@/lib/auth/types';

export default function InventoryDashboard() {
  return (
    <ProtectedRoute
      requiredRoles={[UserRole.ADMIN, UserRole.MANAGER, UserRole.INVENTORY]}
      requiredPermissions={[Permission.VIEW_INVENTORY]}
    >
      {/* Your page content */}
    </ProtectedRoute>
  );
}
```

### 2. Using the Auth Hook

Access authentication state and methods in any component:

```tsx
'use client';

import { useAuth } from '@/lib/auth/AuthContext';

export default function MyComponent() {
  const { 
    user, 
    isAuthenticated, 
    hasPermission, 
    hasRole,
    logout 
  } = useAuth();

  // Check if user has a specific permission
  if (hasPermission(Permission.CREATE_FINANCE)) {
    // Show create button
  }

  // Check if user has a specific role
  if (hasRole(UserRole.ADMIN)) {
    // Show admin features
  }

  return (
    <div>
      {isAuthenticated && <p>Welcome, {user?.name}!</p>}
      <button onClick={logout}>Logout</button>
    </div>
  );
}
```

### 3. Conditional Rendering Based on Permissions

```tsx
'use client';

import { useAuth } from '@/lib/auth/AuthContext';
import { Permission } from '@/lib/auth/types';

export default function FinanceActions() {
  const { hasPermission, hasAnyPermission, hasAllPermissions } = useAuth();

  return (
    <div>
      {/* Show if user has CREATE permission */}
      {hasPermission(Permission.CREATE_FINANCE) && (
        <button>Create Entry</button>
      )}

      {/* Show if user has ANY of the specified permissions */}
      {hasAnyPermission([Permission.EDIT_FINANCE, Permission.DELETE_FINANCE]) && (
        <button>Manage Entries</button>
      )}

      {/* Show if user has ALL specified permissions */}
      {hasAllPermissions([Permission.VIEW_FINANCE, Permission.APPROVE_FINANCE]) && (
        <button>Approve Transactions</button>
      )}
    </div>
  );
}
```

### 4. Higher-Order Component Pattern

Use `withAuth` HOC for cleaner code:

```tsx
import { withAuth } from '@/lib/auth/ProtectedRoute';
import { UserRole, Permission } from '@/lib/auth/types';

function AdminDashboard() {
  return <div>Admin Dashboard Content</div>;
}

export default withAuth(AdminDashboard, {
  requiredRoles: [UserRole.ADMIN],
  requiredPermissions: [Permission.MANAGE_USERS],
});
```

## Route Configuration

Routes are configured in `lib/auth/routes.ts` with their access requirements:

```typescript
{
  path: '/finance/dashboard',
  name: 'Finance Dashboard',
  roles: [UserRole.ADMIN, UserRole.MANAGER, UserRole.FINANCE],
  permissions: [Permission.VIEW_FINANCE],
}
```

## Login Flow

1. User enters credentials on `/login` page
2. Frontend calls `/api/auth/login`
3. Backend validates credentials and returns JWT + user data
4. Frontend stores JWT in HTTP-only cookie
5. User is redirected based on their role:
   - Admin → `/admin/dashboard`
   - Finance → `/finance/dashboard`
   - Inventory → `/inventory/dashboard`
   - HR → `/hr/dashboard`
   - Sales → `/sales/dashboard`
   - Manager → `/manager/dashboard`

## Protected Route Behavior

When a user tries to access a protected route:

1. **Not Authenticated**: Redirected to `/login?redirect=/original-path`
2. **Authenticated but No Permission**: Redirected to `/unauthorized`
3. **Authenticated with Permission**: Access granted

## API Routes

### POST /api/auth/login
Login and set authentication cookie

**Request:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "user": {
    "id": "123",
    "email": "user@example.com",
    "name": "John Doe",
    "role": "finance"
  }
}
```

### GET /api/auth/verify
Verify current authentication status

**Response:**
```json
{
  "success": true,
  "user": { /* user object */ },
  "token": "jwt-token"
}
```

### POST /api/auth/logout
Logout and clear authentication cookie

**Response:**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

## Backend Requirements

Your backend API should:

1. **Validate credentials** and return user data with role
2. **Generate JWT tokens** with user information
3. **Verify JWT tokens** on protected endpoints
4. **Return user permissions** based on role

Example backend user response:
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": "user-123",
    "email": "john@company.com",
    "name": "John Doe",
    "role": "finance",
    "department": "Finance"
  }
}
```

## Security Features

🔒 **HTTP-Only Cookies** - JWT stored in HTTP-only cookies (not accessible via JavaScript)  
🔒 **Secure Flag** - Cookies only sent over HTTPS in production  
🔒 **SameSite Protection** - CSRF protection with SameSite=strict  
🔒 **Client-Side Validation** - Route protection before rendering  
🔒 **Server-Side Validation** - API routes verify tokens  

## Testing

To test different roles:

1. Login with different user accounts
2. Try accessing routes you don't have permission for
3. Verify you're redirected to `/unauthorized`
4. Check that conditional UI elements appear/disappear based on permissions

## Example: Complete Protected Page

```tsx
'use client';

import { ProtectedRoute } from '@/lib/auth/ProtectedRoute';
import { useAuth } from '@/lib/auth/AuthContext';
import { UserRole, Permission } from '@/lib/auth/types';

export default function FinanceDashboard() {
  const { user, hasPermission } = useAuth();

  return (
    <ProtectedRoute
      requiredRoles={[UserRole.ADMIN, UserRole.MANAGER, UserRole.FINANCE]}
      requiredPermissions={[Permission.VIEW_FINANCE]}
    >
      <div className="p-8">
        <h1>Finance Dashboard</h1>
        <p>Welcome, {user?.name}!</p>

        {hasPermission(Permission.CREATE_FINANCE) && (
          <button>Create New Entry</button>
        )}

        {hasPermission(Permission.APPROVE_FINANCE) && (
          <button>Approve Transactions</button>
        )}
      </div>
    </ProtectedRoute>
  );
}
```

## Troubleshooting

### Issue: Infinite redirect loop
**Solution**: Ensure `/login` and `/unauthorized` are not wrapped in `ProtectedRoute`

### Issue: User always redirected to login
**Solution**: Check that `/api/auth/verify` endpoint is working and returning valid user data

### Issue: Permissions not working
**Solution**: Verify that `ROLE_PERMISSIONS` mapping in `types.ts` includes the required permissions for the user's role

## Next Steps

1. ✅ Implement backend authentication API
2. ✅ Add more granular permissions as needed
3. ✅ Create role management UI for admins
4. ✅ Add audit logging for permission checks
5. ✅ Implement refresh token mechanism
