from fastapi import Request, HTTPException, status, Header
from typing import Optional, Annotated
import logging
from app.schemas.tenant import TenantContext

logger = logging.getLogger(__name__)


# Tenant extraction strategies
class TenantExtractionStrategy:
    """Base class for tenant extraction strategies"""
    
    async def extract_tenant_id(self, request: Request) -> Optional[str]:
        """Extract tenant ID from request"""
        raise NotImplementedError


class HeaderTenantStrategy(TenantExtractionStrategy):
    """
    Extract tenant ID from custom header
    Header: X-Tenant-ID: tenant-123
    """
    
    async def extract_tenant_id(
        self,
        request: Request,
        x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
    ) -> Optional[str]:
        if x_tenant_id:
            logger.debug(f"Tenant ID extracted from header: {x_tenant_id}")
            return x_tenant_id
        return None


class SubdomainTenantStrategy(TenantExtractionStrategy):
    """
    Extract tenant ID from subdomain
    Example: tenant1.erp.com -> tenant1
    """
    
    async def extract_tenant_id(self, request: Request) -> Optional[str]:
        host = request.headers.get("host", "")
        
        # Extract subdomain
        parts = host.split(".")
        if len(parts) >= 3:  # subdomain.domain.tld
            subdomain = parts[0]
            logger.debug(f"Tenant ID extracted from subdomain: {subdomain}")
            return subdomain
        
        return None


class PathTenantStrategy(TenantExtractionStrategy):
    """
    Extract tenant ID from URL path
    Example: /api/tenant-123/users -> tenant-123
    """
    
    async def extract_tenant_id(self, request: Request) -> Optional[str]:
        path = request.url.path
        parts = path.split("/")
        
        # Look for tenant ID in path (assuming format /api/{tenant_id}/...)
        if len(parts) >= 3 and parts[1] == "api":
            tenant_id = parts[2]
            if tenant_id and not tenant_id.startswith("_"):  # Avoid internal routes
                logger.debug(f"Tenant ID extracted from path: {tenant_id}")
                return tenant_id
        
        return None


class JWTTenantStrategy(TenantExtractionStrategy):
    """
    Extract tenant ID from JWT token payload
    Requires token to be already validated
    """
    
    async def extract_tenant_id(self, request: Request) -> Optional[str]:
        # This will be populated by the auth middleware
        tenant_id = getattr(request.state, "tenant_id", None)
        if tenant_id:
            logger.debug(f"Tenant ID extracted from JWT: {tenant_id}")
            return tenant_id
        return None


# Tenant extraction with multiple strategies
async def extract_tenant_id_from_request(
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> Optional[str]:
    """
    Extract tenant ID from request using multiple strategies in priority order:
    1. Custom header (X-Tenant-ID)
    2. Subdomain
    3. URL path
    4. JWT token payload
    
    Args:
        request: FastAPI Request object
        x_tenant_id: Optional tenant ID from header
        
    Returns:
        Tenant ID string or None if not found
    """
    strategies = [
        HeaderTenantStrategy(),
        SubdomainTenantStrategy(),
        PathTenantStrategy(),
        JWTTenantStrategy()
    ]
    
    # Try each strategy in order
    for strategy in strategies:
        if isinstance(strategy, HeaderTenantStrategy):
            tenant_id = await strategy.extract_tenant_id(request, x_tenant_id)
        else:
            tenant_id = await strategy.extract_tenant_id(request)
        
        if tenant_id:
            logger.info(f"Tenant ID found: {tenant_id} using {strategy.__class__.__name__}")
            return tenant_id
    
    logger.warning(f"No tenant ID found in request to {request.url.path}")
    return None


async def validate_tenant(tenant_id: str) -> TenantContext:
    """
    Validate tenant ID and retrieve tenant information
    
    In production, this should query the database to:
    1. Verify tenant exists
    2. Check if tenant is active
    3. Retrieve tenant settings
    
    Args:
        tenant_id: Tenant ID to validate
        
    Returns:
        TenantContext object with tenant information
        
    Raises:
        HTTPException: If tenant is invalid or inactive
    """
    # TODO: Replace with actual database query
    # For now, using mock validation
    
    # Mock tenant data (replace with database query)
    mock_tenants = {
        "tenant-1": {
            "id": "tenant-1",
            "name": "Acme Corporation",
            "domain": "acme.erp.com",
            "is_active": True,
            "settings": {"timezone": "UTC", "currency": "USD"}
        },
        "tenant-2": {
            "id": "tenant-2",
            "name": "TechCorp Inc",
            "domain": "techcorp.erp.com",
            "is_active": True,
            "settings": {"timezone": "EST", "currency": "USD"}
        },
        "tenant-3": {
            "id": "tenant-3",
            "name": "Inactive Tenant",
            "domain": "inactive.erp.com",
            "is_active": False,
            "settings": {}
        }
    }
    
    # Check if tenant exists
    tenant_data = mock_tenants.get(tenant_id)
    if not tenant_data:
        logger.error(f"Tenant not found: {tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tenant '{tenant_id}' not found"
        )
    
    # Check if tenant is active
    if not tenant_data.get("is_active", False):
        logger.warning(f"Inactive tenant access attempt: {tenant_id}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Tenant '{tenant_id}' is not active"
        )
    
    logger.info(f"Tenant validated: {tenant_id} - {tenant_data['name']}")
    
    return TenantContext(
        tenant_id=tenant_data["id"],
        tenant_name=tenant_data["name"],
        domain=tenant_data["domain"],
        is_active=tenant_data["is_active"],
        settings=tenant_data.get("settings")
    )


async def get_tenant_context(
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> TenantContext:
    """
    Dependency injection function to extract and validate tenant context
    
    This function:
    1. Extracts tenant ID from request (header, subdomain, path, or JWT)
    2. Validates the tenant exists and is active
    3. Returns tenant context for use in route handlers
    
    Args:
        request: FastAPI Request object
        x_tenant_id: Optional tenant ID from header
        
    Returns:
        TenantContext object with validated tenant information
        
    Raises:
        HTTPException: If no tenant ID found or tenant is invalid/inactive
        
    Usage:
        @app.get("/api/users")
        async def get_users(tenant: TenantContext = Depends(get_tenant_context)):
            # Access tenant information
            print(f"Request from tenant: {tenant.tenant_name}")
            # Query users for this tenant
            users = db.query(User).filter(User.tenant_id == tenant.tenant_id).all()
            return users
    """
    # Extract tenant ID
    tenant_id = await extract_tenant_id_from_request(request, x_tenant_id)
    
    if not tenant_id:
        logger.error(f"No tenant ID provided in request to {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tenant ID is required. Provide via X-Tenant-ID header, subdomain, or URL path"
        )
    
    # Validate and get tenant context
    tenant_context = await validate_tenant(tenant_id)
    
    # Store in request state for access by other dependencies
    request.state.tenant_context = tenant_context
    
    return tenant_context


async def get_optional_tenant_context(
    request: Request,
    x_tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID")
) -> Optional[TenantContext]:
    """
    Optional tenant context dependency - doesn't raise error if no tenant found
    
    Use this for routes that can work with or without tenant context
    
    Args:
        request: FastAPI Request object
        x_tenant_id: Optional tenant ID from header
        
    Returns:
        TenantContext if found and valid, None otherwise
    """
    try:
        return await get_tenant_context(request, x_tenant_id)
    except HTTPException:
        logger.debug("Optional tenant context not found, continuing without tenant")
        return None


def require_tenant_setting(setting_key: str, expected_value: any = None):
    """
    Dependency to require specific tenant setting
    
    Args:
        setting_key: Key to check in tenant settings
        expected_value: Optional expected value for the setting
        
    Returns:
        Dependency function that validates tenant setting
        
    Usage:
        @app.get("/api/feature")
        async def feature_endpoint(
            tenant: TenantContext = Depends(require_tenant_setting("feature_enabled", True))
        ):
            return {"message": "Feature is enabled for this tenant"}
    """
    async def setting_checker(
        tenant: TenantContext = Depends(get_tenant_context)
    ) -> TenantContext:
        settings = tenant.settings or {}
        
        # Check if setting exists
        if setting_key not in settings:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant setting '{setting_key}' not configured"
            )
        
        # Check expected value if provided
        if expected_value is not None and settings[setting_key] != expected_value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Tenant setting '{setting_key}' must be {expected_value}"
            )
        
        return tenant
    
    return setting_checker
