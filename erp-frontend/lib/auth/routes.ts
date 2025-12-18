import { UserRole, Permission } from './types';

// Route configuration for the ERP system
export interface RouteConfig {
    path: string;
    name: string;
    roles?: UserRole[];
    permissions?: Permission[];
    requireAll?: boolean;
    icon?: string;
    children?: RouteConfig[];
}

export const ROUTE_CONFIG: RouteConfig[] = [
    // Public routes
    {
        path: '/login',
        name: 'Login',
    },
    {
        path: '/unauthorized',
        name: 'Unauthorized',
    },

    // Admin routes
    {
        path: '/admin',
        name: 'Admin',
        roles: [UserRole.ADMIN],
        icon: 'shield',
        children: [
            {
                path: '/admin/dashboard',
                name: 'Admin Dashboard',
                roles: [UserRole.ADMIN],
            },
            {
                path: '/admin/users',
                name: 'User Management',
                roles: [UserRole.ADMIN],
                permissions: [Permission.MANAGE_USERS],
            },
            {
                path: '/admin/roles',
                name: 'Role Management',
                roles: [UserRole.ADMIN],
                permissions: [Permission.MANAGE_ROLES],
            },
            {
                path: '/admin/settings',
                name: 'System Settings',
                roles: [UserRole.ADMIN],
                permissions: [Permission.SYSTEM_SETTINGS],
            },
        ],
    },

    // Finance routes
    {
        path: '/finance',
        name: 'Finance',
        roles: [UserRole.ADMIN, UserRole.MANAGER, UserRole.FINANCE],
        permissions: [Permission.VIEW_FINANCE],
        icon: 'dollar',
        children: [
            {
                path: '/finance/dashboard',
                name: 'Finance Dashboard',
                permissions: [Permission.VIEW_FINANCE],
            },
            {
                path: '/finance/journal-entry',
                name: 'Journal Entry',
                permissions: [Permission.CREATE_FINANCE],
            },
            {
                path: '/finance/accounts',
                name: 'Chart of Accounts',
                permissions: [Permission.VIEW_FINANCE],
            },
            {
                path: '/finance/reports',
                name: 'Financial Reports',
                permissions: [Permission.VIEW_FINANCE],
            },
            {
                path: '/finance/approvals',
                name: 'Approvals',
                permissions: [Permission.APPROVE_FINANCE],
            },
        ],
    },

    // Inventory routes
    {
        path: '/inventory',
        name: 'Inventory',
        roles: [UserRole.ADMIN, UserRole.MANAGER, UserRole.INVENTORY],
        permissions: [Permission.VIEW_INVENTORY],
        icon: 'box',
        children: [
            {
                path: '/inventory/dashboard',
                name: 'Inventory Dashboard',
                permissions: [Permission.VIEW_INVENTORY],
            },
            {
                path: '/inventory/items',
                name: 'Items',
                permissions: [Permission.VIEW_INVENTORY],
            },
            {
                path: '/inventory/stock',
                name: 'Stock Management',
                permissions: [Permission.EDIT_INVENTORY],
            },
            {
                path: '/inventory/purchase-orders',
                name: 'Purchase Orders',
                permissions: [Permission.CREATE_INVENTORY],
            },
            {
                path: '/inventory/reports',
                name: 'Inventory Reports',
                permissions: [Permission.VIEW_INVENTORY],
            },
        ],
    },

    // HR routes
    {
        path: '/hr',
        name: 'Human Resources',
        roles: [UserRole.ADMIN, UserRole.MANAGER, UserRole.HR],
        permissions: [Permission.VIEW_HR],
        icon: 'users',
        children: [
            {
                path: '/hr/dashboard',
                name: 'HR Dashboard',
                permissions: [Permission.VIEW_HR],
            },
            {
                path: '/hr/employees',
                name: 'Employees',
                permissions: [Permission.VIEW_HR],
            },
            {
                path: '/hr/attendance',
                name: 'Attendance',
                permissions: [Permission.VIEW_HR],
            },
            {
                path: '/hr/payroll',
                name: 'Payroll',
                permissions: [Permission.VIEW_HR, Permission.EDIT_HR],
                requireAll: true,
            },
            {
                path: '/hr/leave',
                name: 'Leave Management',
                permissions: [Permission.VIEW_HR],
            },
        ],
    },

    // Sales routes
    {
        path: '/sales',
        name: 'Sales',
        roles: [UserRole.ADMIN, UserRole.MANAGER, UserRole.SALES],
        permissions: [Permission.VIEW_SALES],
        icon: 'trending-up',
        children: [
            {
                path: '/sales/dashboard',
                name: 'Sales Dashboard',
                permissions: [Permission.VIEW_SALES],
            },
            {
                path: '/sales/orders',
                name: 'Sales Orders',
                permissions: [Permission.VIEW_SALES],
            },
            {
                path: '/sales/customers',
                name: 'Customers',
                permissions: [Permission.VIEW_SALES],
            },
            {
                path: '/sales/invoices',
                name: 'Invoices',
                permissions: [Permission.CREATE_SALES],
            },
            {
                path: '/sales/reports',
                name: 'Sales Reports',
                permissions: [Permission.VIEW_SALES],
            },
        ],
    },

    // Manager routes
    {
        path: '/manager',
        name: 'Manager',
        roles: [UserRole.ADMIN, UserRole.MANAGER],
        icon: 'briefcase',
        children: [
            {
                path: '/manager/dashboard',
                name: 'Manager Dashboard',
                roles: [UserRole.ADMIN, UserRole.MANAGER],
            },
            {
                path: '/manager/reports',
                name: 'Reports',
                permissions: [Permission.VIEW_REPORTS],
            },
            {
                path: '/manager/analytics',
                name: 'Analytics',
                permissions: [Permission.VIEW_REPORTS],
            },
        ],
    },

    // General dashboard
    {
        path: '/dashboard',
        name: 'Dashboard',
        icon: 'home',
    },
];

// Helper function to check if user can access a route
export function canAccessRoute(
    route: RouteConfig,
    userRole: UserRole,
    userPermissions: Permission[]
): boolean {
    // Check role requirement
    if (route.roles && route.roles.length > 0) {
        if (!route.roles.includes(userRole)) {
            return false;
        }
    }

    // Check permission requirement
    if (route.permissions && route.permissions.length > 0) {
        if (route.requireAll) {
            // User must have ALL required permissions
            return route.permissions.every((permission) =>
                userPermissions.includes(permission)
            );
        } else {
            // User must have at least ONE required permission
            return route.permissions.some((permission) =>
                userPermissions.includes(permission)
            );
        }
    }

    return true;
}

// Get accessible routes for a user
export function getAccessibleRoutes(
    userRole: UserRole,
    userPermissions: Permission[]
): RouteConfig[] {
    return ROUTE_CONFIG.filter((route) =>
        canAccessRoute(route, userRole, userPermissions)
    ).map((route) => ({
        ...route,
        children: route.children?.filter((child) =>
            canAccessRoute(child, userRole, userPermissions)
        ),
    }));
}
