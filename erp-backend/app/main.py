from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging

# Import database
from app.database import init_db, close_db

# Import HTTP client
from app.utils.http_client import HTTPClient

# Import middleware
from app.middleware.tenant import TenantMiddleware, TenantIsolationMiddleware
from app.middleware.rate_limit import RateLimitMiddleware, get_user_key, get_tenant_key

# Import routers
from app.routers import example_tenant, finance, inventory, hr
# from app.routers import auth, users, sales

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for startup and shutdown events
    """
    # Startup
    logger.info("Starting ERP Backend Application...")
    
    # Initialize database
    try:
        await init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {str(e)}")
    
    # Initialize HTTP client
    try:
        await HTTPClient.get_client()
        logger.info("HTTP client initialized successfully")
    except Exception as e:
        logger.error(f"HTTP client initialization failed: {str(e)}")
    
    logger.info("Application started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down ERP Backend Application...")
    
    # Close HTTP client
    try:
        await HTTPClient.close_client()
        logger.info("HTTP client closed")
    except Exception as e:
        logger.error(f"Error closing HTTP client: {str(e)}")
    
    # Close database connections
    try:
        await close_db()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {str(e)}")
    
    logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title="ERP Backend API",
    description="Enterprise Resource Planning System Backend API with RBAC and Multi-Tenancy",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan
)


# Rate Limiting Middleware (add before tenant middleware)
rate_limiter = RateLimitMiddleware(
    app=app.router,
    default_limit=100,  # 100 requests per minute by default
    default_window=60,  # 60 seconds window
    exempt_paths=["/health", "/docs", "/redoc", "/openapi.json", "/api/docs", "/api/redoc"],
    use_redis=False  # Set to True in production with Redis
)

# Configure HR-specific rate limits for public endpoints
rate_limiter.add_route_limit(
    "/api/hr/employees/public/directory",
    requests=10,  # 10 requests
    window=60,  # per minute
    key_func=None  # Use default IP-based key
)

rate_limiter.add_route_limit(
    "/api/hr/employees/public/",
    requests=20,  # 20 requests
    window=60,  # per minute
    key_func=None
)

rate_limiter.add_route_limit(
    "/api/hr/employees/public/contact",
    requests=5,  # 5 requests
    window=3600,  # per hour (3600 seconds)
    key_func=None
)

app.add_middleware(RateLimitMiddleware, **rate_limiter.__dict__)


# Tenant Middleware (add after rate limiting)
app.add_middleware(TenantIsolationMiddleware)
app.add_middleware(TenantMiddleware)


# CORS Middleware Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # Next.js frontend
        "http://localhost:3001",
        # Add production URLs here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Trusted Host Middleware (for production)
# app.add_middleware(
#     TrustedHostMiddleware,
#     allowed_hosts=["localhost", "*.yourdomain.com"]
# )


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "message": "Internal server error",
            "details": str(exc) if app.debug else None
        }
    )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint
    """
    return {
        "status": "healthy",
        "service": "ERP Backend API",
        "version": "1.0.0",
        "features": ["RBAC", "Multi-Tenancy", "JWT Auth"]
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint with API information
    """
    return {
        "message": "ERP Backend API",
        "version": "1.0.0",
        "docs": "/api/docs",
        "health": "/health",
        "features": {
            "authentication": "JWT with RBAC",
            "multi_tenancy": "Header, Subdomain, Path, JWT",
            "modules": ["Finance", "Inventory", "HR", "Sales"]
        }
    }


# Include routers
app.include_router(example_tenant.router)
app.include_router(finance.router)
app.include_router(inventory.router)
app.include_router(hr.router)

# Include other routers (uncomment when created)
# app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
# app.include_router(users.router, prefix="/api/users", tags=["Users"])
# app.include_router(sales.router, prefix="/api/sales", tags=["Sales"])


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=5000,
        reload=True,
        log_level="info"
    )
