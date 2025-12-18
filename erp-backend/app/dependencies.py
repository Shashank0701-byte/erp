from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from datetime import datetime, timedelta
from typing import Optional
from app.config import settings
from app.schemas import TokenData, UserRole, Permission

security = HTTPBearer()


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
    Create JWT access token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(data: dict) -> str:
    """
    Create JWT refresh token
    """
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def verify_token(token: str) -> TokenData:
    """
    Verify and decode JWT token
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        user_id: str = payload.get("sub")
        email: str = payload.get("email")
        role: str = payload.get("role")
        
        if user_id is None or email is None or role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload"
            )
        
        return TokenData(
            user_id=user_id,
            email=email,
            role=UserRole(role),
            exp=datetime.fromtimestamp(payload.get("exp"))
        )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Dependency to get current authenticated user from token
    """
    token = credentials.credentials
    return verify_token(token)


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
