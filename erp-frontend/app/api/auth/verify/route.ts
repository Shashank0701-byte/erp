import { NextRequest, NextResponse } from 'next/server';

const BACKEND_API_URL = process.env.BACKEND_API_URL || 'http://localhost:5000';

export async function GET(request: NextRequest) {
    try {
        // Get the auth token from cookies
        const token = request.cookies.get('auth-token')?.value;

        if (!token) {
            return NextResponse.json(
                { message: 'No authentication token found' },
                { status: 401 }
            );
        }

        // Verify token with backend
        const backendResponse = await fetch(`${BACKEND_API_URL}/api/auth/verify`, {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`,
                'Content-Type': 'application/json',
            },
        });

        if (!backendResponse.ok) {
            return NextResponse.json(
                { message: 'Invalid or expired token' },
                { status: 401 }
            );
        }

        const data = await backendResponse.json();

        return NextResponse.json(
            {
                success: true,
                user: data.user,
                token: token,
            },
            { status: 200 }
        );
    } catch (error) {
        console.error('Verify error:', error);
        return NextResponse.json(
            { message: 'Authentication verification failed' },
            { status: 500 }
        );
    }
}
