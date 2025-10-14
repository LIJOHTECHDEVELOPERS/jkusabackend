from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List, Optional
import logging
from app.database import get_db
from app.models.admin import Admin
from app.models.admin_role import AdminRole as AdminRoleModel  # SQLAlchemy model - RENAMED
from app.schemas.admin_role import AdminRoleCreate, AdminRoleUpdate, AdminRole as AdminRoleSchema  # Pydantic schema - RENAMED
from app.auth.auth import get_current_admin
from app.auth.permissions import require_manage_admins, check_permission

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin/roles", tags=["admin_roles"])

def is_super_admin(admin: Admin) -> bool:
    """Check if admin has super_admin role"""
    return admin.role and admin.role.name == "super_admin"

def format_role_response(role: AdminRoleModel) -> dict:
    """Format role object for response"""
    return {
        "id": role.id,
        "name": role.name,
        "description": role.description,
        "permissions": role.permissions,
        "created_at": role.created_at.isoformat() if role.created_at else None,
        "updated_at": role.updated_at.isoformat() if role.updated_at else None
    }

@router.post("/", response_model=dict)
def create_role(
    role: AdminRoleCreate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_manage_admins)
):
    """Create a new role (requires manage_roles permission)"""
    if not check_permission(current_admin, "manage_roles"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create roles"
        )

    # Check if role name already exists
    existing_role = db.query(AdminRoleModel).filter(AdminRoleModel.name == role.name).first()
    if existing_role:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role name already exists"
        )

    try:
        db_role = AdminRoleModel(
            name=role.name,
            description=role.description,
            permissions=role.permissions
        )
        db.add(db_role)
        db.commit()
        db.refresh(db_role)
        return {
            "message": "Role created successfully",
            "role": format_role_response(db_role)
        }
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create role"
        )

@router.get("/", response_model=dict)
def list_roles(
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by name or description"),
    sort_by: str = Query("created_at", description="Sort by field"),
    sort_order: str = Query("desc", regex="^(asc|desc)$", description="Sort order")
):
    """List all roles with pagination and filtering"""
    try:
        query = db.query(AdminRoleModel)

        # Apply search filter
        if search:
            query = query.filter(
                or_(
                    AdminRoleModel.name.ilike(f"%{search}%"),
                    AdminRoleModel.description.ilike(f"%{search}%")
                )
            )

        # Get total count before pagination
        total = query.count()

        # Apply sorting
        if hasattr(AdminRoleModel, sort_by):
            sort_column = getattr(AdminRoleModel, sort_by)
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(AdminRoleModel.created_at.desc())

        # Apply pagination
        offset = (page - 1) * per_page
        roles = query.offset(offset).limit(per_page).all()

        # Calculate total pages
        total_pages = (total + per_page - 1) // per_page

        # Format response
        role_list = [format_role_response(role) for role in roles]

        return {
            "roles": role_list,
            "total": total,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1
        }
    except Exception as e:
        logger.error(f"Error listing roles: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve roles"
        )

@router.get("/{role_id}", response_model=dict)
def get_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(get_current_admin)
):
    """Get a specific role by ID"""
    role = db.query(AdminRoleModel).filter(AdminRoleModel.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )
    return format_role_response(role)

@router.put("/{role_id}", response_model=dict)
def update_role(
    role_id: int,
    role_update: AdminRoleUpdate,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_manage_admins)
):
    """Update a role's information (requires manage_roles permission)"""
    if not check_permission(current_admin, "manage_roles"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update roles"
        )

    role = db.query(AdminRoleModel).filter(AdminRoleModel.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Prevent modifying super_admin role unless current admin is super_admin
    if role.name == "super_admin" and not is_super_admin(current_admin):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only super admins can modify the super_admin role"
        )

    try:
        # Check if name is being updated and if it's already taken
        if role_update.name and role_update.name != role.name:
            existing_role = db.query(AdminRoleModel).filter(AdminRoleModel.name == role_update.name).first()
            if existing_role:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Role name already taken"
                )

        # Update fields that are provided
        update_data = role_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(role, field, value)

        if hasattr(role, 'updated_at'):
            from sqlalchemy import func
            role.updated_at = func.now()
        
        db.commit()
        db.refresh(role)

        return {
            "message": "Role updated successfully",
            "role": format_role_response(role)
        }
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update role"
        )

@router.delete("/{role_id}", response_model=dict)
def delete_role(
    role_id: int,
    db: Session = Depends(get_db),
    current_admin: Admin = Depends(require_manage_admins)
):
    """Delete a role (requires manage_roles permission)"""
    if not check_permission(current_admin, "manage_roles"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to delete roles"
        )

    role = db.query(AdminRoleModel).filter(AdminRoleModel.id == role_id).first()
    if not role:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Role not found"
        )

    # Prevent deleting super_admin role
    if role.name == "super_admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete super_admin role"
        )

    # Check if role is assigned to any admins
    assigned_admins = db.query(Admin).filter(Admin.role_id == role_id).count()
    if assigned_admins > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete role assigned to {assigned_admins} admin(s). Please reassign them first."
        )

    try:
        db.delete(role)
        db.commit()
        return {"message": "Role deleted successfully"}
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting role: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete role"
        )

@router.get("/permissions/available", response_model=dict)
def list_available_permissions(
    current_admin: Admin = Depends(get_current_admin)
):
    """List all available permissions that can be assigned to roles"""
    available_permissions = [
        "manage_admins",
        "manage_roles",
        "manage_users",
        "manage_news",
        "manage_events",
        "manage_announcements",
        "manage_settings",
        "view_reports",
        "manage_payments"
    ]
    
    return {
        "permissions": available_permissions,
        "description": {
            "manage_admins": "Create, update, and delete admin users",
            "manage_roles": "Create and modify roles and permissions",
            "manage_users": "Manage regular application users",
            "manage_news": "Create, edit, and delete news articles",
            "manage_events": "Create, edit, and delete events",
            "manage_announcements": "Create, edit, and delete announcements",
            "manage_settings": "Modify system settings",
            "view_reports": "Access reports and analytics",
            "manage_payments": "Handle payment-related operations"
        }
    }