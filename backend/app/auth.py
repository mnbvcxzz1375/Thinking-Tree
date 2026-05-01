"""
JWT Authentication middleware and utilities.
"""
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from app.config import settings

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Bearer token security
security = HTTPBearer()


class TokenData(BaseModel):
    """Token payload data."""
    user_id: str
    username: str
    role: str
    school_id: Optional[str] = None


class UserInDB(BaseModel):
    """User model for database."""
    id: str
    username: str
    hashed_password: str
    role: str  # admin, teacher, observer
    school_id: Optional[str] = None
    is_active: bool = True


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: Token payload data
        expires_delta: Optional custom expiration time
        
    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, 
        settings.jwt_secret_key, 
        algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> TokenData:
    """
    Decode and validate a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        TokenData with user information
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token, 
            settings.jwt_secret_key, 
            algorithms=[settings.jwt_algorithm]
        )
        
        user_id: str = payload.get("sub")
        username: str = payload.get("username")
        role: str = payload.get("role")
        school_id: str = payload.get("school_id")
        
        if user_id is None or username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return TokenData(
            user_id=user_id,
            username=username,
            role=role,
            school_id=school_id
        )
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    FastAPI dependency to get current authenticated user.
    
    Usage:
        @router.get("/protected")
        async def protected_route(user: TokenData = Depends(get_current_user)):
            return {"user": user.username}
    """
    token = credentials.credentials
    return decode_token(token)


async def get_current_active_user(
    current_user: TokenData = Depends(get_current_user)
) -> TokenData:
    """Get current active user (can be extended to check user status)."""
    # Here you could add additional checks like:
    # - Is the user still active?
    # - Has the user's role changed?
    # - Is the token blacklisted?
    return current_user


class RoleChecker:
    """
    Dependency to check if user has required role.
    
    Usage:
        require_admin = RoleChecker(["admin"])
        require_teacher = RoleChecker(["admin", "teacher"])
        
        @router.get("/admin-only")
        async def admin_route(user: TokenData = Depends(require_admin)):
            return {"message": "Admin access"}
    """
    
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles
    
    async def __call__(
        self, 
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        if current_user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{current_user.role}' not in allowed roles: {self.allowed_roles}"
            )
        return current_user


# Common role checkers
require_admin = RoleChecker(["admin"])
require_teacher = RoleChecker(["admin", "teacher"])
require_observer = RoleChecker(["admin", "teacher", "observer"])


class SchoolIsolation:
    """
    Dependency to ensure user can only access their school's data.
    
    Usage:
        @router.get("/schools/{school_id}/data")
        async def school_data(
            school_id: str,
            user: TokenData = Depends(SchoolIsolation(school_id))
        ):
            return {"school": school_id}
    """
    
    def __init__(self, required_school_id: Optional[str] = None):
        self.required_school_id = required_school_id
    
    async def __call__(
        self,
        current_user: TokenData = Depends(get_current_user)
    ) -> TokenData:
        # Admin can access any school
        if current_user.role == "admin":
            return current_user
        
        # Check school isolation
        if self.required_school_id and current_user.school_id != self.required_school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: Cannot access other school's data"
            )
        
        return current_user
