import { NextRequest, NextResponse } from "next/server";

export async function POST(request: NextRequest) {
    try {
        const { email, password } = await request.json();

        // Validate input
        if (!email || !password) {
            return NextResponse.json(
                { message: "Email and password are required" },
                { status: 400 }
            );
        }

        // TODO: Replace with actual authentication logic
        // This should verify credentials against your database
        const response = await fetch(`${process.env.BACKEND_API_URL}/auth/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ email, password }),
        });

        if (!response.ok) {
            const error = await response.json();
            return NextResponse.json(
                { message: error.message || "Authentication failed" },
                { status: response.status }
            );
        }

        const data = await response.json();
        const token = data.token;

        // Create response
        const res = NextResponse.json(
            { message: "Login successful" },
            { status: 200 }
        );

        // Set HTTP-only cookie with JWT token
        res.cookies.set({
            name: "auth-token",
            value: token,
            httpOnly: true,
            secure: process.env.NODE_ENV === "production",
            sameSite: "strict",
            maxAge: 60 * 60 * 24 * 7, // 7 days
            path: "/",
        });

        return res;
    } catch (error) {
        console.error("Login error:", error);
        return NextResponse.json(
            { message: "Internal server error" },
            { status: 500 }
        );
    }
}
