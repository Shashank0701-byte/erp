'use client';

import { useEffect, ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from './AuthContext';
import { UserRole, Permission } from './types';

interface ProtectedRouteProps {
    children: ReactNode;
    requiredRoles?: UserRole[];
    requiredPermissions?: Permission[];
    requireAll?: boolean; // If true, user must have ALL permissions; if false, ANY permission
    fallbackUrl?: string;
}

export function ProtectedRoute({
    children,
    requiredRoles,
    requiredPermissions,
    requireAll = false,
    fallbackUrl = '/login',
}: ProtectedRouteProps) {
    const router = useRouter();
    const pathname = usePathname();
    const { isAuthenticated, isLoading, user, hasRole, hasPermission, hasAllPermissions, hasAnyPermission } = useAuth();

    useEffect(() => {
        if (isLoading) return;

        // Not authenticated - redirect to login
        if (!isAuthenticated || !user) {
            router.push(`${fallbackUrl}?redirect=${encodeURIComponent(pathname)}`);
            return;
        }

        // Check role requirements
        if (requiredRoles && requiredRoles.length > 0) {
            if (!hasRole(requiredRoles)) {
                router.push('/unauthorized');
                return;
            }
        }

        // Check permission requirements
        if (requiredPermissions && requiredPermissions.length > 0) {
            const hasRequiredPermissions = requireAll
                ? hasAllPermissions(requiredPermissions)
                : hasAnyPermission(requiredPermissions);

            if (!hasRequiredPermissions) {
                router.push('/unauthorized');
                return;
            }
        }
    }, [
        isAuthenticated,
        isLoading,
        user,
        requiredRoles,
        requiredPermissions,
        requireAll,
        router,
        pathname,
        fallbackUrl,
        hasRole,
        hasAllPermissions,
        hasAnyPermission,
    ]);

    // Show loading state
    if (isLoading) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
                <div className="text-center">
                    <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                    <p className="mt-4 text-gray-600 dark:text-gray-400">Loading...</p>
                </div>
            </div>
        );
    }

    // Not authenticated
    if (!isAuthenticated || !user) {
        return null;
    }

    // Check role requirements
    if (requiredRoles && requiredRoles.length > 0 && !hasRole(requiredRoles)) {
        return null;
    }

    // Check permission requirements
    if (requiredPermissions && requiredPermissions.length > 0) {
        const hasRequiredPermissions = requireAll
            ? hasAllPermissions(requiredPermissions)
            : hasAnyPermission(requiredPermissions);

        if (!hasRequiredPermissions) {
            return null;
        }
    }

    return <>{children}</>;
}

// Higher-order component for page-level protection
export function withAuth<P extends object>(
    Component: React.ComponentType<P>,
    options?: Omit<ProtectedRouteProps, 'children'>
) {
    return function ProtectedComponent(props: P) {
        return (
            <ProtectedRoute {...options}>
                <Component {...props} />
            </ProtectedRoute>
        );
    };
}
