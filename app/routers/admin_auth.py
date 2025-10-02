# app/routers/admin_auth.py

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from pydantic import BaseModel, EmailStr
import logging
from typing import Optional, List
from app.database import get_db
from app.models.admin import Admin  # SQLAlchemy model
from app.schemas.admin import Token  # Import only Token from schemas
from app.auth.auth import verify_password, get_password_hash, create_access_token, get_current_admin

# --------------------
# 🛠️ FIX 1: Initialize the logger
# --------------------
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/auth", tags=["admin_auth"])

# JSON Login Model
class LoginRequest(BaseModel):
    username: str  # Can be username or email
    password: str

# Local AdminCreate to avoid import issues
class AdminCreateLocal(BaseModel):
    first_name: str
    last_name: str
    email: str
    phone_number: str
    username: str
    password: str

# Admin Update Model
class AdminUpdateLocal(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

# Admin response model for user info
class AdminResponse(BaseModel):
    id: int
    username: str
    first_name: str
    last_name: str
    email: str
    phone_number: str
    is_active: bool
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        from_attributes = True

# Enhanced Token response with user data
class TokenWithUser(BaseModel):
    access_token: str
    token_type: str
    user_data: AdminResponse

# Pagination response model
class AdminListResponse(BaseModel):
    admins: List[AdminResponse]
    total: int
    page: int
    per_page: int
    total_pages: int

# Local helper functions to avoid import issues
def get_admin_by_identifier(db: Session, identifier: str):
    """Get admin by username or email"""
    try:
        # Direct SQLAlchemy query without relying on external functions
        return db.query(Admin).filter(
            or_(Admin.username == identifier, Admin.email == identifier)
        ).first()
    except Exception as e:
        # print(f"Error querying admin by identifier: {e}") # Removed print, logger is preferred
        logger.error(f"Error querying admin by identifier: {e}")
        # Fallback: try username first, then email
        try:
            admin = db.query(Admin).filter(Admin.username == identifier).first()
            if admin:
                return admin
            return db.query(Admin).filter(Admin.email == identifier).first()
        except Exception as fallback_error:
            # print(f"Fallback query also failed: {fallback_error}") # Removed print
            logger.error(f"Fallback query also failed: {fallback_error}")
            return None

def get_admin_by_username(db: Session, username: str):
    """Get admin by username only"""
    try:
        return db.query(Admin).filter(Admin.username == username).first()
    except Exception as e:
        # print(f"Error querying admin by username: {e}") # Removed print
        logger.error(f"Error querying admin by username: {e}")
        return None

def get_admin_by_email(db: Session, email: str):
    """Get admin by email only"""
    try:
        return db.query(Admin).filter(Admin.email == email).first()
    except Exception as e:
        # print(f"Error querying admin by email: {e}") # Removed print
        logger.error(f"Error querying admin by email: {e}")
        return None

def get_admin_by_id(db: Session, admin_id: int):
    """Get admin by ID"""
    try:
        return db.query(Admin).filter(Admin.id == admin_id).first()
    except Exception as e:
        # print(f"Error querying admin by ID: {e}") # Removed print
        logger.error(f"Error querying admin by ID: {e}")
        return None

def create_token_response(admin: Admin) -> dict:
    """Create standardized token response with user data"""
    access_token = create_access_token(data={"sub": admin.username, "type": "admin"})
    
    # Create user data response
    user_data = {
        "id": admin.id,
        "username": admin.username,
        "first_name": getattr(admin, 'first_name', ''),
        "last_name": getattr(admin, 'last_name', ''),
        "email": getattr(admin, 'email', ''),
        "phone_number": getattr(admin, 'phone_number', ''),
        "is_active": getattr(admin, 'is_active', True),
        "role": "admin",
        "name": f"{getattr(admin, 'first_name', '')} {getattr(admin, 'last_name', '')}".strip()
    }
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user_data": user_data
    }

def format_admin_response(admin: Admin) -> dict:
    """Format admin object for response"""
    return {
        "id": admin.id,
        "username": admin.username,
        "first_name": getattr(admin, 'first_name', ''),
        "last_name": getattr(admin, 'last_name', ''),
        "email": getattr(admin, 'email', ''),
        "phone_number": getattr(admin, 'phone_number', ''),
        "is_active": getattr(admin, 'is_active', True),
        "created_at": getattr(admin, 'created_at', None).isoformat() if getattr(admin, 'created_at', None) else None,
        "updated_at": getattr(admin, 'updated_at', None).isoformat() if getattr(admin, 'updated_at', None) else None,
        "role": "admin",
        "name": f"{getattr(admin, 'first_name', '')} {getattr(admin, 'last_name', '')}".strip()
    }

@router.post("/register-admin", response_model=dict)
def register_admin(admin: AdminCreateLocal, db: Session = Depends(get_db), current_admin=Depends(get_current_admin)):
    """Register a new admin (requires existing admin authentication)"""
    
    # Check if username already exists
    existing_admin = get_admin_by_username(db, admin.username)
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_admin = get_admin_by_email(db, admin.email)
    if existing_admin:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Email already registered"
        )
    
    # Create new admin
    try:
        hashed_password = get_password_hash(admin.password)
        db_admin = Admin(
            first_name=admin.first_name,
            last_name=admin.last_name,
            email=admin.email,
            phone_number=admin.phone_number,
            username=admin.username,
            hashed_password=hashed_password,
            is_active=True  # Ensure new admin is active
        )
        
        db.add(db_admin)
        db.commit()
        db.refresh(db_admin)
        
        # Return token with user data
        return create_token_response(db_admin)
    
    except Exception as e:
        db.rollback()
        # print(f"Error creating admin: {e}") # Removed print
        logger.error(f"Error creating admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin"
        )

@router.get("/admins", response_model=dict)
def list_admins(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, username, or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """List all admins with pagination and filtering"""
    
    try:
        # Base query
        query = db.query(Admin)
        
        # Apply search filter
        if search:
            search_filter = or_(
                Admin.first_name.ilike(f"%{search}%"),
                Admin.last_name.ilike(f"%{search}%"),
                Admin.username.ilike(f"%{search}%"),
                Admin.email.ilike(f"%{search}%")
            )
            query = query.filter(search_filter)
        
        # Apply active status filter
        if is_active is not None:
            query = query.filter(Admin.is_active == is_active)
        
        # Get total count before pagination
        total = query.count()
        
        # Apply sorting
        if hasattr(Admin, sort_by):
            sort_column = getattr(Admin, sort_by)
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            # Default sort by created_at desc
            if hasattr(Admin, 'created_at'):
                query = query.order_by(Admin.created_at.desc())
        
        # Apply pagination
        offset = (page - 1) * per_page
        admins = query.offset(offset).limit(per_page).all()
        
        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page
        
        # Format response
        admin_list = [format_admin_response(admin) for admin in admins]
        
        return {
            "admins": admin_list,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
        
    except Exception as e:
        # print(f"Error listing admins: {e}") # Removed print
        logger.error(f"Error listing admins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admins"
        )

@router.get("/admins/{admin_id}", response_model=dict)
def get_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get a specific admin by ID"""
    
    admin = get_admin_by_id(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    return format_admin_response(admin)

@router.put("/admins/{admin_id}", response_model=dict)
def update_admin(
    admin_id: int,
    admin_update: AdminUpdateLocal,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update an admin's information"""
    
    # Get the admin to update
    admin = get_admin_by_id(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    try:
        # Check if username is being updated and if it's already taken
        if admin_update.username and admin_update.username != admin.username:
            existing_admin = get_admin_by_username(db, admin_update.username)
            if existing_admin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Check if email is being updated and if it's already taken
        if admin_update.email and admin_update.email != admin.email:
            existing_admin = get_admin_by_email(db, admin_update.email)
            if existing_admin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
        
        # Update fields that are provided
        update_data = admin_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "password":
                # Hash the new password
                admin.hashed_password = get_password_hash(value)
            else:
                setattr(admin, field, value)
        
        # Update the updated_at timestamp if the field exists
        if hasattr(admin, 'updated_at'):
            from sqlalchemy import func
            admin.updated_at = func.now()
        
        db.commit()
        db.refresh(admin)
        
        return {
            "message": "Admin updated successfully",
            "admin": format_admin_response(admin)
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        # print(f"Error updating admin: {e}") # Removed print
        logger.error(f"Error updating admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update admin"
        )

@router.delete("/admins/{admin_id}")
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Delete an admin (soft delete by setting is_active to False)"""
    
    # Prevent self-deletion
    if admin_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    admin = get_admin_by_id(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    try:
        # Soft delete by setting is_active to False
        admin.is_active = False
        
        # Update the updated_at timestamp if the field exists
        if hasattr(admin, 'updated_at'):
            from sqlalchemy import func
            admin.updated_at = func.now()
        
        db.commit()
        
        return {"message": "Admin deactivated successfully"}
        
    except Exception as e:
        db.rollback()
        # print(f"Error deleting admin: {e}") # Removed print
        logger.error(f"Error deleting admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete admin"
        )

@router.post("/admins/{admin_id}/activate")
def activate_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Activate a deactivated admin"""
    
    admin = get_admin_by_id(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    try:
        admin.is_active = True
        
        # Update the updated_at timestamp if the field exists
        if hasattr(admin, 'updated_at'):
            from sqlalchemy import func
            admin.updated_at = func.now()
        
        db.commit()
        
        return {"message": "Admin activated successfully"}
        
    except Exception as e:
        db.rollback()
        # print(f"Error activating admin: {e}") # Removed print
        logger.error(f"Error activating admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate admin"
        )

@router.post("/login", response_model=dict)
def login_json(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login admin with username/email and password (JSON data)"""
    
    logger.debug(f"Login attempt for: {login_data.username}")
    
    try:
        # Try to find admin by username or email
        admin = get_admin_by_identifier(db, login_data.username)
        
        if not admin:
            logger.debug(f"Admin not found for identifier: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # --------------------
        # 🛠️ FIX 2: Truncate the password to 72 bytes for bcrypt compatibility
        # --------------------
        # Encode the password to bytes and truncate to the first 72 bytes.
        plain_password_truncated = login_data.password.encode('utf-8')[:72]
        
        # Verify password
        logger.debug(f"Verifying password for admin: {admin.username}")
        if not verify_password(plain_password_truncated, admin.hashed_password):
            logger.debug(f"Password verification failed for admin: {admin.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if admin is active
        if hasattr(admin, 'is_active') and not admin.is_active:
            logger.debug(f"Admin account disabled: {admin.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"Login successful for admin: {admin.username}")
        
        # Return token with user data
        try:
            logger.debug("Creating access token")
            token_response = create_token_response(admin)
            logger.debug("Token created successfully")
            return token_response
        except Exception as e:
            logger.error(f"Error creating access token: {str(e)}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create access token: {str(e)}"
            )
    
    except HTTPException:
        # Re-raise explicit HTTPException errors without logging as unexpected error
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/me", response_model=dict)
def get_current_admin_info(current_admin: Admin = Depends(get_current_admin)):
    """Get current admin information"""
    return format_admin_response(current_admin)

@router.put("/me", response_model=dict)
def update_current_admin(
    admin_update: AdminUpdateLocal,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update current admin's own information"""
    
    try:
        # Check if username is being updated and if it's already taken
        if admin_update.username and admin_update.username != current_admin.username:
            existing_admin = get_admin_by_username(db, admin_update.username)
            if existing_admin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        # Check if email is being updated and if it's already taken
        if admin_update.email and admin_update.email != current_admin.email:
            existing_admin = get_admin_by_email(db, admin_update.email)
            if existing_admin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
        
        # Update fields that are provided (excluding is_active for self-update)
        update_data = admin_update.dict(exclude_unset=True, exclude={'is_active'})
        
        for field, value in update_data.items():
            if field == "password":
                # Hash the new password
                current_admin.hashed_password = get_password_hash(value)
            else:
                setattr(current_admin, field, value)
        
        # Update the updated_at timestamp if the field exists
        if hasattr(current_admin, 'updated_at'):
            from sqlalchemy import func
            current_admin.updated_at = func.now()
        
        db.commit()
        db.refresh(current_admin)
        
        return {
            "message": "Profile updated successfully",
            "admin": format_admin_response(current_admin)
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        # print(f"Error updating current admin: {e}") # Removed print
        logger.error(f"Error updating current admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.post("/refresh-token", response_model=dict)
def refresh_access_token(current_admin: Admin = Depends(get_current_admin)):
    """Refresh access token for current admin"""
    return create_token_response(current_admin)

@router.post("/refresh", response_model=dict)
def refresh_access_token_alias(current_admin: Admin = Depends(get_current_admin)):
    """Refresh access token for current admin (alias for /refresh-token)"""
    return create_token_response(current_admin)

@router.post("/logout")
def logout():
    """Logout admin (client should discard the token)"""
    return {"message": "Successfully logged out"}

@router.get("/verify-token", response_model=dict)
def verify_token(current_admin: Admin = Depends(get_current_admin)):
    """Verify if the current token is valid and return user info"""
    admin_data = format_admin_response(current_admin)
    admin_data.update({
        "valid": True,
        "type": "admin"
    })
    return admin_data