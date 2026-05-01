"""
Authentication router for login, register, and token management.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
from app.database import get_db
from app.auth import (
    create_access_token,
    verify_password,
    get_password_hash,
    get_current_user,
    TokenData,
    decode_token
)

router = APIRouter()


# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    role: str = "teacher"  # admin, teacher, observer
    school_id: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str
    role: str


class UserInfo(BaseModel):
    user_id: str
    username: str
    role: str
    school_id: Optional[str] = None


# In-memory user store (replace with database in production)
# This is a simplified version for development
_users_db = {
    "admin": {
        "id": "user-001",
        "username": "admin",
        "hashed_password": get_password_hash("admin123"),
        "role": "admin",
        "school_id": None,
        "is_active": True
    },
    "teacher": {
        "id": "user-002",
        "username": "teacher",
        "hashed_password": get_password_hash("teacher123"),
        "role": "teacher",
        "school_id": "school-001",
        "is_active": True
    }
}


@router.post("/login", response_model=TokenResponse)
async def login(request: LoginRequest):
    """
    Authenticate user and return JWT token.
    
    Default credentials for development:
    - admin / admin123 (admin role)
    - teacher / teacher123 (teacher role)
    """
    user = _users_db.get(request.username)
    
    if not user or not verify_password(request.password, user["hashed_password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": user["id"],
            "username": user["username"],
            "role": user["role"],
            "school_id": user.get("school_id")
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        user_id=user["id"],
        username=user["username"],
        role=user["role"]
    )


@router.post("/register", response_model=TokenResponse)
async def register(request: RegisterRequest):
    """
    Register a new user.
    
    In production, this would:
    - Validate school_id exists
    - Send verification email
    - Require admin approval for certain roles
    """
    # Check if username already exists
    if request.username in _users_db:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Create new user
    user_id = f"user-{len(_users_db) + 1:03d}"
    new_user = {
        "id": user_id,
        "username": request.username,
        "hashed_password": get_password_hash(request.password),
        "role": request.role,
        "school_id": request.school_id,
        "is_active": True
    }
    
    _users_db[request.username] = new_user
    
    # Create access token
    access_token = create_access_token(
        data={
            "sub": new_user["id"],
            "username": new_user["username"],
            "role": new_user["role"],
            "school_id": new_user.get("school_id")
        }
    )
    
    return TokenResponse(
        access_token=access_token,
        user_id=new_user["id"],
        username=new_user["username"],
        role=new_user["role"]
    )


@router.get("/me", response_model=UserInfo)
async def get_me(current_user: TokenData = Depends(get_current_user)):
    """Get current user information."""
    return UserInfo(
        user_id=current_user.user_id,
        username=current_user.username,
        role=current_user.role,
        school_id=current_user.school_id
    )


@router.post("/refresh")
async def refresh_token(current_user: TokenData = Depends(get_current_user)):
    """Refresh the current user's token."""
    access_token = create_access_token(
        data={
            "sub": current_user.user_id,
            "username": current_user.username,
            "role": current_user.role,
            "school_id": current_user.school_id
        }
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
