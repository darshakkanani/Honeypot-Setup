"""
Authentication and authorization endpoints
"""

from fastapi import APIRouter, HTTPException, Depends, Request, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr
from typing import Optional
import jwt
from datetime import datetime, timedelta
import secrets
import structlog

from ..core.config import config
from ..core.database import get_db
from ..core.redis import get_redis
from ..core.security import (
    hash_password, verify_password, create_access_token, 
    create_refresh_token, verify_token
)
from ..models.user import User
from ..utils.email import send_email

logger = structlog.get_logger()
router = APIRouter(prefix="/api/auth", tags=["authentication"])
security = HTTPBearer()

# Request/Response models
class LoginRequest(BaseModel):
    username: str
    password: str
    remember_me: bool = False

class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    invite_code: Optional[str] = None

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/login")
async def login(
    request: Request,
    login_data: LoginRequest,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """Authenticate user and return JWT tokens"""
    try:
        # Get user from database
        user = await User.get_by_username(db, login_data.username)
        
        if not user:
            logger.warning("login_failed", username=login_data.username, reason="user_not_found")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if account is locked
        if user.locked_until and user.locked_until > datetime.utcnow():
            logger.warning("login_failed", username=login_data.username, reason="account_locked")
            raise HTTPException(status_code=423, detail="Account temporarily locked")
        
        # Verify password
        if not verify_password(login_data.password, user.password_hash):
            # Increment failed attempts
            await user.increment_failed_attempts(db)
            logger.warning("login_failed", username=login_data.username, reason="invalid_password")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if not user.is_active:
            logger.warning("login_failed", username=login_data.username, reason="account_disabled")
            raise HTTPException(status_code=403, detail="Account disabled")
        
        # Reset failed attempts and update last login
        await user.reset_failed_attempts(db)
        await user.update_last_login(db)
        
        # Create tokens
        token_data = {"sub": user.username, "user_id": str(user.id), "role": user.role}
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        # Store refresh token in Redis
        if redis:
            await redis.setex(f"refresh:{user.id}", 30 * 24 * 3600, refresh_token)
        
        # Log successful login
        await user.log_action(db, "LOGIN", {"success": True}, request.client.host)
        
        logger.info("login_successful", username=user.username, user_id=str(user.id))
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": config.JWT_EXPIRY_HOURS * 3600,
            "user": {
                "id": str(user.id),
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "permissions": user.get_permissions()
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("login_error", username=login_data.username, error=str(e))
        raise HTTPException(status_code=500, detail="Login failed")

@router.post("/logout")
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """Logout user and blacklist token"""
    try:
        # Decode token to get user info
        payload = jwt.decode(credentials.credentials, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        user_id = payload.get("user_id")
        
        # Blacklist the token
        if redis:
            exp = payload.get("exp")
            if exp:
                ttl = exp - int(datetime.utcnow().timestamp())
                if ttl > 0:
                    await redis.setex(f"blacklist:{credentials.credentials}", ttl, "1")
        
        # Remove refresh token
        if redis and user_id:
            await redis.delete(f"refresh:{user_id}")
        
        # Log logout
        if user_id:
            user = await User.get_by_id(db, user_id)
            if user:
                await user.log_action(db, "LOGOUT", {"success": True}, request.client.host)
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error("logout_error", error=str(e))
        return {"message": "Logged out"}

@router.post("/refresh")
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """Refresh access token using refresh token"""
    try:
        payload = jwt.decode(refresh_data.refresh_token, config.JWT_SECRET, algorithms=[config.JWT_ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = payload.get("user_id")
        username = payload.get("sub")
        
        # Verify refresh token in Redis
        if redis:
            stored_token = await redis.get(f"refresh:{user_id}")
            if not stored_token or stored_token != refresh_data.refresh_token:
                raise HTTPException(status_code=401, detail="Invalid refresh token")
        
        # Get user to check if still active
        user = await User.get_by_id(db, user_id)
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="User not found or inactive")
        
        # Create new access token
        token_data = {"sub": username, "user_id": user_id, "role": user.role}
        new_access_token = create_access_token(token_data)
        
        return {
            "access_token": new_access_token,
            "token_type": "bearer",
            "expires_in": config.JWT_EXPIRY_HOURS * 3600
        }
        
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Refresh token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

@router.get("/me")
async def get_current_user(
    username: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Get current user information"""
    user = await User.get_by_username(db, username)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "role": user.role,
        "permissions": user.get_permissions(),
        "created_at": user.created_at.isoformat(),
        "last_login": user.last_login.isoformat() if user.last_login else None,
        "is_active": user.is_active
    }

@router.post("/register")
async def register(
    register_data: RegisterRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """Register new user (admin only or with invite code)"""
    # Check if registration is open or invite code is valid
    if register_data.invite_code != config.INVITE_CODE:
        raise HTTPException(status_code=403, detail="Invalid invite code")
    
    # Check if username already exists
    existing_user = await User.get_by_username(db, register_data.username)
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Check if email already exists
    existing_email = await User.get_by_email(db, register_data.email)
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
    # Create new user
    user_data = {
        "username": register_data.username,
        "email": register_data.email,
        "password_hash": hash_password(register_data.password),
        "role": "user",  # Default role
        "is_active": True
    }
    
    user = await User.create(db, user_data)
    
    # Send welcome email
    background_tasks.add_task(
        send_email,
        register_data.email,
        "Welcome to SecureHoney",
        f"Welcome {register_data.username}! Your account has been created successfully."
    )
    
    logger.info("user_registered", username=register_data.username, user_id=str(user.id))
    
    return {
        "message": "User registered successfully",
        "user": {
            "id": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }

@router.post("/password-reset")
async def request_password_reset(
    reset_data: PasswordResetRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """Request password reset"""
    user = await User.get_by_email(db, reset_data.email)
    
    if not user:
        # Don't reveal if email exists
        return {"message": "If the email exists, a reset link has been sent"}
    
    # Generate reset token
    reset_token = secrets.token_urlsafe(32)
    
    # Store reset token in Redis (expires in 1 hour)
    if redis:
        await redis.setex(f"password_reset:{reset_token}", 3600, str(user.id))
    
    # Send reset email
    reset_url = f"{config.FRONTEND_URL}/reset-password?token={reset_token}"
    background_tasks.add_task(
        send_email,
        user.email,
        "Password Reset Request",
        f"Click here to reset your password: {reset_url}"
    )
    
    logger.info("password_reset_requested", user_id=str(user.id))
    
    return {"message": "If the email exists, a reset link has been sent"}

@router.post("/password-reset/confirm")
async def confirm_password_reset(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db),
    redis = Depends(get_redis)
):
    """Confirm password reset with token"""
    if not redis:
        raise HTTPException(status_code=500, detail="Password reset not available")
    
    # Get user ID from reset token
    user_id = await redis.get(f"password_reset:{reset_data.token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Get user
    user = await User.get_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Update password
    await user.update_password(db, hash_password(reset_data.new_password))
    
    # Delete reset token
    await redis.delete(f"password_reset:{reset_data.token}")
    
    logger.info("password_reset_completed", user_id=str(user.id))
    
    return {"message": "Password reset successfully"}

@router.post("/change-password")
async def change_password(
    password_data: ChangePasswordRequest,
    username: str = Depends(verify_token),
    db: AsyncSession = Depends(get_db)
):
    """Change user password"""
    user = await User.get_by_username(db, username)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Verify current password
    if not verify_password(password_data.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    
    # Update password
    await user.update_password(db, hash_password(password_data.new_password))
    
    logger.info("password_changed", user_id=str(user.id))
    
    return {"message": "Password changed successfully"}

@router.post("/verify")
async def verify_token_endpoint(username: str = Depends(verify_token)):
    """Verify if token is valid"""
    return {"valid": True, "username": username}
