'use client';

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { useRouter } from 'next/navigation';
import { User, AuthState, UserRole, Permission, ROLE_PERMISSIONS } from './types';

interface AuthContextType extends AuthState {
    login: (email: string, password: string) => Promise<void>;
    logout: () => Promise<void>;
    hasPermission: (permission: Permission) => boolean;
    hasRole: (role: UserRole | UserRole[]) => boolean;
    hasAnyPermission: (permissions: Permission[]) => boolean;
    hasAllPermissions: (permissions: Permission[]) => boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
    const router = useRouter();
    const [authState, setAuthState] = useState<AuthState>({
        user: null,
        isAuthenticated: false,
        isLoading: true,
        token: null,
    });

    // Check authentication status on mount
    useEffect(() => {
        checkAuth();
    }, []);

    const checkAuth = async () => {
        try {
            // Check if user is authenticated by calling a verify endpoint
            const response = await fetch('/api/auth/verify', {
                credentials: 'include',
            });

            if (response.ok) {
                const data = await response.json();
                setAuthState({
                    user: data.user,
                    isAuthenticated: true,
                    isLoading: false,
                    token: data.token || null,
                });
            } else {
                setAuthState({
                    user: null,
                    isAuthenticated: false,
                    isLoading: false,
                    token: null,
                });
            }
        } catch (error) {
            console.error('Auth check failed:', error);
            setAuthState({
                user: null,
                isAuthenticated: false,
                isLoading: false,
                token: null,
            });
        }
    };

    const login = async (email: string, password: string) => {
        try {
            const response = await fetch('/api/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email, password }),
                credentials: 'include',
            });

            if (!response.ok) {
                const error = await response.json();
                throw new Error(error.message || 'Login failed');
            }

            const data = await response.json();

            // Get user permissions based on role
            const permissions = ROLE_PERMISSIONS[data.user.role as UserRole] || [];

            const user: User = {
                ...data.user,
                permissions,
            };

            setAuthState({
                user,
                isAuthenticated: true,
                isLoading: false,
                token: data.token || null,
            });

            // Redirect based on role
            redirectBasedOnRole(user.role);
        } catch (error) {
            throw error;
        }
    };

    const logout = async () => {
        try {
            await fetch('/api/auth/logout', {
                method: 'POST',
                credentials: 'include',
            });
        } catch (error) {
            console.error('Logout error:', error);
        } finally {
            setAuthState({
                user: null,
                isAuthenticated: false,
                isLoading: false,
                token: null,
            });
            router.push('/login');
        }
    };

    const hasPermission = (permission: Permission): boolean => {
        if (!authState.user) return false;
        return authState.user.permissions.includes(permission);
    };

    const hasRole = (role: UserRole | UserRole[]): boolean => {
        if (!authState.user) return false;
        if (Array.isArray(role)) {
            return role.includes(authState.user.role);
        }
        return authState.user.role === role;
    };

    const hasAnyPermission = (permissions: Permission[]): boolean => {
        if (!authState.user) return false;
        return permissions.some((permission) =>
            authState.user!.permissions.includes(permission)
        );
    };

    const hasAllPermissions = (permissions: Permission[]): boolean => {
        if (!authState.user) return false;
        return permissions.every((permission) =>
            authState.user!.permissions.includes(permission)
        );
    };

    const redirectBasedOnRole = (role: UserRole) => {
        switch (role) {
            case UserRole.ADMIN:
                router.push('/admin/dashboard');
                break;
            case UserRole.FINANCE:
                router.push('/finance/dashboard');
                break;
            case UserRole.INVENTORY:
                router.push('/inventory/dashboard');
                break;
            case UserRole.HR:
                router.push('/hr/dashboard');
                break;
            case UserRole.SALES:
                router.push('/sales/dashboard');
                break;
            case UserRole.MANAGER:
                router.push('/manager/dashboard');
                break;
            default:
                router.push('/dashboard');
        }
    };

    return (
        <AuthContext.Provider
            value={{
                ...authState,
                login,
                logout,
                hasPermission,
                hasRole,
                hasAnyPermission,
                hasAllPermissions,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth() {
    const context = useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
    }
    return context;
}
