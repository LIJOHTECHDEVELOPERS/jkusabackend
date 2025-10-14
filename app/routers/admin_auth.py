from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from pydantic import BaseModel
from typing import Optional, List
import logging
from app.database import get_db
from app.models.admin import Admin
from app.models.admin_role import AdminRole
from app.schemas.admin import AdminCreate, Admin, TokenWithUser, AdminListResponse
from app.auth.auth import verify_password, get_password_hash, create_access_token, get_current_admin
from app.auth.permissions import require_manage_admins, check_permission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/auth", tags=["admin_auth"])

# JSON Login Model
class LoginRequest(BaseModel):
    username: str
    password: str

# Helper functions
def get_admin_by_identifier(db: Session, identifier: str):
    """Get admin by username or email"""
    try:
        return db.query(Admin).filter(
            or_(Admin.username == identifier, Admin.email == identifier)
        ).first()
    except Exception as e:
        logger.error(f"Error querying admin by identifier: {e}")
        return None

def get_admin_by_username(db: Session, username: str):
    """Get admin by username only"""
    try:
        return db.query(Admin).filter(Admin.username == username).first()
    except Exception as e:
        logger.error(f"Error querying admin by username: {e}")
        return None

def get_admin_by_email(db: Session, email: str):
    """Get admin by email only"""
    try:
        return db.query(Admin).filter(Admin.email == email).first()
    except Exception as e:
        logger.error(f"Error querying admin by email: {e}")
        return None

def get_admin_by_id(db: Session, admin_id: int):
    """Get admin by ID"""
    try:
        return db.query(Admin).filter(Admin.id == admin_id).first()
    except Exception as e:
        logger.error(f"Error querying admin by ID: {e}")
        return None

def format_admin_response(admin: Admin) -> dict:
    """Format admin object for response including role"""
    return {
        "id": admin.id,
        "username": admin.username,
        "first_name": getattr(admin, 'first_name', ''),
        "last_name": getattr(admin, 'last_name', ''),
        "email": getattr(admin, 'email', ''),
        "phone_number": getattr(admin, 'phone_number', ''),
        "is_active": getattr(admin, 'is_active', True),
        "role": {
            "id": admin.role.id,
            "name": admin.role.name,
            "description": admin.role.description,
            "permissions": admin.role.permissions
        } if admin.role else None,
        "created_at": getattr(admin, 'created_at', None).isoformat() if getattr(admin, 'created_at', None) else None,
        "updated_at": getattr(admin, 'updated_at', None).isoformat() if getattr(admin, 'updated_at', None) else None,
    }

def create_token_response(admin: Admin) -> dict:
    """Create standardized token response with user data including role"""
    access_token = create_access_token(data={"sub": admin.username, "type": "admin"})
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_data": format_admin_response(admin)
    }

@router.post("/register-admin", response_model=TokenWithUser)
def register_admin(
    admin: AdminCreate, 
    db: Session = Depends(get_db), 
    current_admin: Admin = Depends(require_manage_admins)
):
    """Register a new admin (requires manage_admins permission)"""
    
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
    
    # Validate role_id if provided
    role = None
    if admin.role_id:
        role = db.query(AdminRole).filter(AdminRole.id == admin.role_id).first()
        if not role:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid role_id"
            )
        
        # Only super admins can create other super admins
        if role.name == "super_admin" and not current_admin.is_super_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only super admins can create super admin accounts"
            )
    else:
        # Get default role (admin) if not specified
        role = db.query(AdminRole).filter(AdminRole.name == "admin").first()
    
    try:
        hashed_password = get_password_hash(admin.password)
        db_admin = Admin(
            first_name=admin.first_name,
            last_name=admin.last_name,
            email=admin.email,
            phone_number=admin.phone_number,
            username=admin.username,
            hashed_password=hashed_password,
            is_active=True,
            role_id=role.id if role else None
        )
        
        db.add(db_admin)
        db.commit()
        db.refresh(db_admin)
        
        return create_token_response(db_admin)
    
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create admin"
        )

@router.get("/admins", response_model=AdminListResponse)
def list_admins(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name, username, or email"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    role_id: Optional[int] = Query(None, description="Filter by role"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """List all admins with pagination, filtering, and role information"""
    
    try:
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
        
        # Apply role filter
        if role_id is not None:
            query = query.filter(Admin.role_id == role_id)
        
        total = query.count()
        
        # Apply sorting
        if hasattr(Admin, sort_by):
            sort_column = getattr(Admin, sort_by)
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            if hasattr(Admin, 'created_at'):
                query = query.order_by(Admin.created_at.desc())
        
        offset = (page - 1) * per_page
        admins = query.offset(offset).limit(per_page).all()
        
        total_pages = (total + per_page - 1) // per_page
        admin_list = [Admin(**format_admin_response(admin)) for admin in admins]
        
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
        logger.error(f"Error listing admins: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admins"
        )

@router.get("/admins/{admin_id}", response_model=Admin)
def get_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get a specific admin by ID with role information"""
    
    admin = get_admin_by_id(db, admin_id)
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin not found"
        )
    
    return Admin(**format_admin_response(admin))

@router.put("/admins/{admin_id}", response_model=dict)
def update_admin(
    admin_id: int,
    admin_update: AdminCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update an admin's information including role"""
    
    # Check permission
    if not check_permission(current_admin, "manage_admins") and current_admin.id != admin_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update other admins"
        )
    
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
        
        # Validate and check role change permissions
        if admin_update.role_id is not None:
            # Check if user has permission to change roles
            if not check_permission(current_admin, "manage_admins"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to change roles"
                )
            
            # Validate role exists
            new_role = db.query(AdminRole).filter(AdminRole.id == admin_update.role_id).first()
            if not new_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid role_id"
                )
            
            # Only super admins can assign super_admin role
            if new_role.name == "super_admin" and not current_admin.is_super_admin():
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only super admins can assign super_admin role"
                )
            
            # Prevent removing super_admin from the last super admin
            if admin.role and admin.role.name == "super_admin":
                super_admin_count = db.query(Admin).join(AdminRole).filter(
                    AdminRole.name == "super_admin",
                    Admin.is_active == True
                ).count()
                if super_admin_count <= 1 and new_role.name != "super_admin":
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Cannot remove super_admin role from the last super admin"
                    )
        
        update_data = admin_update.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if field == "password":
                admin.hashed_password = get_password_hash(value)
            else:
                setattr(admin, field, value)
        
        if hasattr(admin, 'updated_at'):
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
        logger.error(f"Error updating admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update admin"
        )

@router.delete("/admins/{admin_id}", response_model=dict)
def delete_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_manage_admins)
):
    """Delete an admin (soft delete by setting is_active to False)"""
    
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
    
    # Prevent deleting the last super admin
    if admin.role and admin.role.name == "super_admin":
        super_admin_count = db.query(Admin).join(AdminRole).filter(
            AdminRole.name == "super_admin",
            Admin.is_active == True
        ).count()
        if super_admin_count <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete the last super admin"
            )
    
    try:
        admin.is_active = False
        
        if hasattr(admin, 'updated_at'):
            admin.updated_at = func.now()
        
        db.commit()
        
        return {"message": "Admin deactivated successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete admin"
        )

@router.post("/admins/{admin_id}/activate", response_model=dict)
def activate_admin(
    admin_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_manage_admins)
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
        
        if hasattr(admin, 'updated_at'):
            admin.updated_at = func.now()
        
        db.commit()
        
        return {"message": "Admin activated successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error activating admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate admin"
        )

@router.post("/login", response_model=TokenWithUser)
def login_json(login_data: LoginRequest, db: Session = Depends(get_db)):
    """Login admin with username/email and password (JSON data)"""
    
    logger.debug(f"Login attempt for: {login_data.username}")
    
    try:
        admin = get_admin_by_identifier(db, login_data.username)
        
        if not admin:
            logger.debug(f"Admin not found for identifier: {login_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        plain_password_truncated = login_data.password.encode('utf-8')[:72]
        
        logger.debug(f"Verifying password for admin: {admin.username}")
        if not verify_password(plain_password_truncated, admin.hashed_password):
            logger.debug(f"Password verification failed for admin: {admin.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username/email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if hasattr(admin, 'is_active') and not admin.is_active:
            logger.debug(f"Admin account disabled: {admin.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin account is disabled",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        logger.debug(f"Login successful for admin: {admin.username}")
        
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
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login endpoint: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )

@router.get("/me", response_model=Admin)
def get_current_admin_info(current_admin: Admin = Depends(get_current_admin)):
    """Get current admin information including role and permissions"""
    return Admin(**format_admin_response(current_admin))

@router.put("/me", response_model=dict)
def update_current_admin(
    admin_update: AdminCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Update current admin's own information (cannot change own role)"""
    
    try:
        if admin_update.username and admin_update.username != current_admin.username:
            existing_admin = get_admin_by_username(db, admin_update.username)
            if existing_admin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        
        if admin_update.email and admin_update.email != current_admin.email:
            existing_admin = get_admin_by_email(db, admin_update.email)
            if existing_admin:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already taken"
                )
        
        # Exclude is_active and role_id for self-update
        update_data = admin_update.dict(exclude_unset=True, exclude={'is_active', 'role_id'})
        
        for field, value in update_data.items():
            if field == "password":
                current_admin.hashed_password = get_password_hash(value)
            else:
                setattr(current_admin, field, value)
        
        if hasattr(current_admin, 'updated_at'):
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
        logger.error(f"Error updating current admin: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update profile"
        )

@router.post("/refresh-token", response_model=TokenWithUser)
def refresh_access_token(current_admin: Admin = Depends(get_current_admin)):
    """Refresh access token for current admin"""
    return create_token_response(current_admin)

@router.post("/refresh", response_model=TokenWithUser)
def refresh_access_token_alias(current_admin: Admin = Depends(get_current_admin)):
    """Refresh access token for current admin (alias for /refresh-token)"""
    return create_token_response(current_admin)

@router.post("/logout", response_model=dict)
def logout():
    """Logout admin (client should discard the token)"""
    return {"message": "Successfully logged out"}

@router.get("/verify-token", response_model=Admin)
def verify_token(current_admin: Admin = Depends(get_current_admin)):
    """Verify if the current token is valid and return user info with role"""
    admin_data = format_admin_response(current_admin)
    admin_data.update({
        "valid": True,
        "type": "admin"
    })
    return admin_data