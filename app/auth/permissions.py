from fastapi import Depends, HTTPException, status
from app.models.admin import Admin
from app.auth.auth import get_current_admin
import logging

logger = logging.getLogger(__name__)

def check_permission(admin: Admin, permission: str) -> bool:
    """
    Check if the admin has the specified permission.
    Returns True if the admin is a super_admin or has the permission in their role.
    """
    try:
        # Super admins have all permissions
        if admin.is_super_admin():
            logger.debug(f"Admin {admin.username} is super_admin, granting permission: {permission}")
            return True
        
        # Check if the admin has a role and the specified permission
        if admin.role and admin.role.permissions:
            has_permission = admin.role.permissions.get(permission, False) or admin.role.permissions.get("all", False)
            logger.debug(f"Checking permission {permission} for admin {admin.username}: {has_permission}")
            return has_permission
        
        logger.debug(f"Admin {admin.username} has no role or permissions defined")
        return False
    except Exception as e:
        logger.error(f"Error checking permission {permission} for admin {admin.username}: {e}")
        return False

def require_manage_admins(current_admin: Admin = Depends(get_current_admin)):
    """
    Dependency to ensure the current admin has manage_admins permission or is a super_admin.
    Raises HTTPException if permission is not granted.
    """
    try:
        if not (current_admin.is_super_admin() or check_permission(current_admin, "manage_admins")):
            logger.warning(f"Admin {current_admin.username} denied access to manage admins")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to manage admins"
            )
        logger.debug(f"Admin {current_admin.username} granted manage_admins permission")
        return current_admin
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in require_manage_admins for admin {current_admin.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while checking permissions"
        )

def require_manage_roles(current_admin: Admin = Depends(get_current_admin)):
    """
    Dependency to ensure the current admin has manage_roles permission or is a super_admin.
    Raises HTTPException if permission is not granted.
    """
    try:
        if not (current_admin.is_super_admin() or check_permission(current_admin, "manage_roles")):
            logger.warning(f"Admin {current_admin.username} denied access to manage roles")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to manage roles"
            )
        logger.debug(f"Admin {current_admin.username} granted manage_roles permission")
        return current_admin
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in require_manage_roles for admin {current_admin.username}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error while checking permissions"
        )