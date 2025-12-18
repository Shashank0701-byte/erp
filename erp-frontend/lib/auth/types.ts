// User roles in the ERP system
export enum UserRole {
    ADMIN = 'admin',
    MANAGER = 'manager',
    FINANCE = 'finance',
    INVENTORY = 'inventory',
    HR = 'hr',
    SALES = 'sales',
    VIEWER = 'viewer',
}

// Permissions for different actions
export enum Permission {
    // Finance permissions
    VIEW_FINANCE = 'view_finance',
    CREATE_FINANCE = 'create_finance',
    EDIT_FINANCE = 'edit_finance',
    DELETE_FINANCE = 'delete_finance',
    APPROVE_FINANCE = 'approve_finance',

    // Inventory permissions
    VIEW_INVENTORY = 'view_inventory',
    CREATE_INVENTORY = 'create_inventory',
    EDIT_INVENTORY = 'edit_inventory',
    DELETE_INVENTORY = 'delete_inventory',

    // HR permissions
    VIEW_HR = 'view_hr',
    CREATE_HR = 'create_hr',
    EDIT_HR = 'edit_hr',
    DELETE_HR = 'delete_hr',

    // Sales permissions
    VIEW_SALES = 'view_sales',
    CREATE_SALES = 'create_sales',
    EDIT_SALES = 'edit_sales',
    DELETE_SALES = 'delete_sales',

    // Admin permissions
    MANAGE_USERS = 'manage_users',
    MANAGE_ROLES = 'manage_roles',
    VIEW_REPORTS = 'view_reports',
    SYSTEM_SETTINGS = 'system_settings',
}

// User interface
export interface User {
    id: string;
    email: string;
    name: string;
    role: UserRole;
    permissions: Permission[];
    department?: string;
    avatar?: string;
}

// Auth state interface
export interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    token: string | null;
}

// Role to permissions mapping
export const ROLE_PERMISSIONS: Record<UserRole, Permission[]> = {
    [UserRole.ADMIN]: Object.values(Permission), // Admin has all permissions

    [UserRole.MANAGER]: [
        Permission.VIEW_FINANCE,
        Permission.VIEW_INVENTORY,
        Permission.VIEW_HR,
        Permission.VIEW_SALES,
        Permission.VIEW_REPORTS,
        Permission.CREATE_FINANCE,
        Permission.CREATE_INVENTORY,
        Permission.EDIT_FINANCE,
        Permission.EDIT_INVENTORY,
    ],

    [UserRole.FINANCE]: [
        Permission.VIEW_FINANCE,
        Permission.CREATE_FINANCE,
        Permission.EDIT_FINANCE,
        Permission.DELETE_FINANCE,
        Permission.APPROVE_FINANCE,
    ],

    [UserRole.INVENTORY]: [
        Permission.VIEW_INVENTORY,
        Permission.CREATE_INVENTORY,
        Permission.EDIT_INVENTORY,
        Permission.DELETE_INVENTORY,
    ],

    [UserRole.HR]: [
        Permission.VIEW_HR,
        Permission.CREATE_HR,
        Permission.EDIT_HR,
        Permission.DELETE_HR,
    ],

    [UserRole.SALES]: [
        Permission.VIEW_SALES,
        Permission.CREATE_SALES,
        Permission.EDIT_SALES,
        Permission.DELETE_SALES,
    ],

    [UserRole.VIEWER]: [
        Permission.VIEW_FINANCE,
        Permission.VIEW_INVENTORY,
        Permission.VIEW_HR,
        Permission.VIEW_SALES,
    ],
};
