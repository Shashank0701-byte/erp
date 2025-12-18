from fastapi import Depends, HTTPException, status, Request, Cookie
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt, ExpiredSignatureError
from datetime import datetime, timedelta
from typing import Optional
import logging
from app.config import settings
from app.schemas import TokenData, UserRole, Permission

# Configure logger
logger = logging.getLogger(__name__)

# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


# Role to permissions mapping
ROLE_PERMISSIONS = {
    UserRole.ADMIN: list(Permission),  # All permissions
    UserRole.MANAGER: [
        Permission.VIEW_FINANCE, Permission.VIEW_INVENTORY, 
        Permission.VIEW_HR, Permission.VIEW_SALES,
        Permission.VIEW_REPORTS, Permission.CREATE_FINANCE,
        Permission.CREATE_INVENTORY, Permission.EDIT_FINANCE,
        Permission.EDIT_INVENTORY
    ],
    UserRole.FINANCE: [
        Permission.VIEW_FINANCE, Permission.CREATE_FINANCE,
        Permission.EDIT_FINANCE, Permission.DELETE_FINANCE,
        Permission.APPROVE_FINANCE
    ],
    UserRole.INVENTORY: [
        Permission.VIEW_INVENTORY, Permission.CREATE_INVENTORY,
        Permission.EDIT_INVENTORY, Permission.DELETE_INVENTORY
    ],
    UserRole.HR: [
        Permission.VIEW_HR, Permission.CREATE_HR,
        Permission.EDIT_HR, Permission.DELETE_HR
    ],
    UserRole.SALES: [
        Permission.VIEW_SALES, Permission.CREATE_SALES,
        Permission.EDIT_SALES, Permission.DELETE_SALES
    ],
    UserRole.VIEWER: [
        Permission.VIEW_FINANCE, Permission.VIEW_INVENTORY,
        Permission.VIEW_HR, Permission.VIEW_SALES
    ]
}


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create JWT access token with secure defaults
    
    Args:
        data: Dictionary containing user data (sub, email, role)
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    # Set expiration time
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    # Add standard JWT claims
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),  # Issued at
        "type": "access"  # Token type
    })
    
    # Encode token
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    logger.info(f"Access token created for user: {data.get('email')}")
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token with extended expiration
    
    Args:
        data: Dictionary containing user data
        
    Returns:
        Encoded refresh token string
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    
    logger.info(f"Refresh token created for user: {data.get('email')}")
    return encoded_jwt


def extract_token_from_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = None,
    auth_token: Optional[str] = None
) -> Optional[str]:
    """
    Extract JWT token from multiple sources with priority:
    1. Authorization header (Bearer token)
    2. Cookie (auth-token)
    3. Query parameter (for special cases)
    
    Args:
        request: FastAPI Request object
        credentials: HTTP Bearer credentials from header
        auth_token: Token from cookie
        
    Returns:
        Token string or None if not found
    """
    # Priority 1: Authorization header
    if credentials and credentials.credentials:
        logger.debug("Token extracted from Authorization header")
        return credentials.credentials
    
    # Priority 2: Cookie
    if auth_token:
        logger.debug("Token extracted from cookie")
        return auth_token
    
    # Priority 3: Query parameter (use with caution, not recommended for production)
    token_from_query = request.query_params.get("token")
    if token_from_query:
        logger.warning("Token extracted from query parameter - not recommended for production")
        return token_from_query
    
    return None


def verify_token(token: str, token_type: str = "access") -> TokenData:
    """
    Verify and decode JWT token with comprehensive validation
    
    Args:
        token: JWT token string
        token_type: Expected token type ('access' or 'refresh')
        
    Returns:
        TokenData object with user information
        
    Raises:
        HTTPException: If token is invalid, expired, or malformed
    """
    try:
        # Decode token
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        
        # Validate token type
        if payload.get("type") != token_type:
            logger.warning(f"Invalid token type. Expected: {token_type}, Got: {payload.get('type')}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token type. Expected {token_type} token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Extract required fields
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        # Validate required fields
        if not user_id or not email or not role:
            logger.error("Token missing required fields")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload - missing required fields",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate role
        try:
            user_role = UserRole(role)
        except ValueError:
            logger.error(f"Invalid role in token: {role}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid role in token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check expiration
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            if exp_datetime < datetime.utcnow():
                logger.warning(f"Token expired for user: {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )
        
        logger.info(f"Token verified successfully for user: {email}")
        
        return TokenData(
            user_id=user_id,
            email=email,
            role=user_role,
            exp=datetime.fromtimestamp(exp_timestamp) if exp_timestamp else None
        )
        
    except ExpiredSignatureError:
        logger.warning("Token signature has expired")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except JWTError as e:
        logger.error(f"JWT validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except Exception as e:
        logger.error(f"Unexpected error during token verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    auth_token: Optional[str] = Cookie(None, alias="auth-token")
) -> TokenData:
    """
    Dependency injection function to extract and validate JWT from request
    
    Supports multiple token sources:
    - Authorization: Bearer <token> header
    - auth-token cookie
    - token query parameter (not recommended for production)
    
    Args:
        request: FastAPI Request object
        credentials: Optional Bearer token from Authorization header
        auth_token: Optional token from cookie
        
    Returns:
        TokenData object containing validated user information
        
    Raises:
        HTTPException: If no token found or validation fails
        
    Usage:
        @app.get("/protected")
        async def protected_route(current_user: TokenData = Depends(get_current_user)):
            return {"user_id": current_user.user_id}
    """
    # Extract token from request
    token = extract_token_from_request(request, credentials, auth_token)
    
    if not token:
        logger.warning(f"No authentication token found in request to {request.url.path}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated - no token provided",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify and decode token
    return verify_token(token, token_type="access")


def get_user_permissions(role: UserRole) -> list[Permission]:
    """
    Get permissions for a user role
    """
    return ROLE_PERMISSIONS.get(role, [])


def require_permission(required_permission: Permission):
    """
    Dependency to require specific permission
    """
    async def permission_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        user_permissions = get_user_permissions(current_user.role)
        
        if required_permission not in user_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required permission: {required_permission.value}"
            )
        
        return current_user
    
    return permission_checker


def require_role(required_roles: list[UserRole]):
    """
    Dependency to require specific role(s)
    """
    async def role_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied. Required roles: {[r.value for r in required_roles]}"
            )
        
        return current_user
    
    return role_checker


def require_any_permission(required_permissions: list[Permission]):
    """
    Dependency to require any of the specified permissions
    """
    async def permission_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        user_permissions = get_user_permissions(current_user.role)
        
        if not any(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required any of: {[p.value for p in required_permissions]}"
            )
        
        return current_user
    
    return permission_checker


def require_all_permissions(required_permissions: list[Permission]):
    """
    Dependency to require all specified permissions
    """
    async def permission_checker(
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        user_permissions = get_user_permissions(current_user.role)
        
        if not all(perm in user_permissions for perm in required_permissions):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission denied. Required all of: {[p.value for p in required_permissions]}"
            )
        
        return current_user
    
    return permission_checker
