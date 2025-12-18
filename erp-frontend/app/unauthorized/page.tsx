'use client';

import { useRouter } from 'next/navigation';
import { useAuth } from '@/lib/auth/AuthContext';

export default function UnauthorizedPage() {
    const router = useRouter();
    const { user } = useAuth();

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-red-50 via-orange-50 to-yellow-50 dark:from-gray-900 dark:via-red-950 dark:to-orange-950 px-4">
            <div className="max-w-md w-full text-center">
                {/* Error Icon */}
                <div className="inline-flex items-center justify-center w-24 h-24 bg-gradient-to-br from-red-500 to-orange-600 rounded-full mb-6 shadow-2xl">
                    <svg
                        className="w-12 h-12 text-white"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                    >
                        <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                        />
                    </svg>
                </div>

                {/* Error Message */}
                <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
                    Access Denied
                </h1>
                <p className="text-lg text-gray-600 dark:text-gray-400 mb-2">
                    You don't have permission to access this page.
                </p>
                {user && (
                    <p className="text-sm text-gray-500 dark:text-gray-500 mb-8">
                        Your role: <span className="font-semibold text-gray-700 dark:text-gray-300">{user.role}</span>
                    </p>
                )}

                {/* Action Buttons */}
                <div className="flex flex-col sm:flex-row gap-3 justify-center">
                    <button
                        onClick={() => router.back()}
                        className="px-6 py-3 bg-white dark:bg-gray-800 text-gray-700 dark:text-gray-300 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors font-medium"
                    >
                        Go Back
                    </button>
                    <button
                        onClick={() => router.push('/dashboard')}
                        className="px-6 py-3 bg-gradient-to-r from-indigo-600 to-purple-600 text-white rounded-lg hover:from-indigo-700 hover:to-purple-700 transition-all font-medium shadow-lg"
                    >
                        Go to Dashboard
                    </button>
                </div>

                {/* Help Text */}
                <div className="mt-8 p-4 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
                    <p className="text-sm text-gray-600 dark:text-gray-400">
                        If you believe you should have access to this page, please contact your system administrator.
                    </p>
                </div>
            </div>
        </div>
    );
}
