import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.admin import Admin
from app.models.admin_role import AdminRole
from app.auth.auth import get_password_hash
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Validate database URL
if not SQLALCHEMY_DATABASE_URL:
    logger.error("DATABASE_URL environment variable is not set")
    raise ValueError("DATABASE_URL environment variable is not set. Please set it in the .env file.")

# Create database engine and session
try:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Database engine created successfully")
except Exception as e:
    logger.error(f"Failed to create database engine: {e}")
    raise

def create_super_admin():
    """Create a super admin user if it doesn't exist"""
    db = SessionLocal()
    try:
        # Check if super_admin role exists, create if not
        super_admin_role = db.query(AdminRole).filter(AdminRole.name == "super_admin").first()
        if not super_admin_role:
            super_admin_role = AdminRole(
                name="super_admin",
                description="Super Administrator with full access",
                permissions={"all": True},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(super_admin_role)
            db.commit()
            db.refresh(super_admin_role)
            logger.info("Created super_admin role")
        else:
            logger.info("super_admin role already exists")

        # Check if admin@jkusa.org exists
        existing_admin = db.query(Admin).filter(
            Admin.email == "superadmin@jkusa.org"
        ).first()
        if existing_admin:
            logger.info("Admin user superadmin@jkusa.org already exists")
            return

        # Create super admin user
        password = "jkusa202500200"  # Replace with your desired password
        hashed_password = get_password_hash(password)
        new_admin = Admin(
            first_name="Elijah",
            last_name="Kibuchi",
            email="superadmin@jkusa.org",
            phone_number="1234567890",
            username="superadmin@jkusa.org",
            hashed_password=hashed_password,
            is_active=True,
            role_id=super_admin_role.id,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.add(new_admin)
        db.commit()
        db.refresh(new_admin)
        logger.info(f"Created super admin user: superadmin@jkusa.org with role ID {super_admin_role.id}")
        logger.info(f"Use password: {password} to log in")

    except Exception as e:
        db.rollback()
        logger.error(f"Error creating super admin: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    try:
        create_super_admin()
        logger.info("Super admin creation script completed successfully")
    except Exception as e:
        logger.error(f"Script failed: {e}")