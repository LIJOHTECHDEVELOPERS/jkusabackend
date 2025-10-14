from app.models.admin import Admin as AdminModel

def is_super_admin(admin: AdminModel) -> bool:
    """Check if admin has super_admin role"""
    return admin.role and admin.role.name == "super_admin"