# create_initial_admin.py
import os
import sys
from sqlalchemy.orm import Session
import bcrypt

# Import ALL models to ensure SQLAlchemy relationships are properly configured
try:
    from app.models import admin, news, event, gallery
    # Try to import optional models
    try:
        from app.models import member
    except ImportError:
        pass
    try:
        from app.models import donation
    except ImportError:
        pass
except ImportError as e:
    print(f"Note: Some model imports may have failed: {e}")
    pass

# Now import the specific models we need
from app.models.admin import Admin

# Use bcrypt directly with passlib-compatible format
import bcrypt

def create_passlib_compatible_hash(password: str) -> str:
    """
    Create a bcrypt hash that's compatible with passlib verification.
    Uses bcrypt directly but produces the same format passlib expects.
    """
    if not isinstance(password, str):
        password = str(password)
    
    # Truncate to 72 bytes
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        password_bytes = password_bytes[:72]
    
    # Create hash with bcrypt directly
    # Use $2b$ prefix which is what passlib expects
    salt = bcrypt.gensalt(rounds=12, prefix=b"2b")
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    return hashed.decode('utf-8')

# --- CONFIGURATION (Change these details) ---
FIRST_ADMIN_USERNAME = os.getenv("FIRST_ADMIN_USERNAME", "superadmin")
FIRST_ADMIN_EMAIL = os.getenv("FIRST_ADMIN_EMAIL", "admin@jkusa.org")
FIRST_ADMIN_PASSWORD = os.getenv("FIRST_ADMIN_PASSWORD", "Elijah@10519")
FIRST_ADMIN_FIRST_NAME = "Super"
FIRST_ADMIN_LAST_NAME = "Admin"
FIRST_ADMIN_PHONE = "+254706400432"

def hash_password_with_bcrypt(password: str) -> str:
    """
    Hash password directly using bcrypt without passlib.
    This avoids the bcrypt version error with passlib.
    """
    # Ensure password is a string
    if not isinstance(password, str):
        password = str(password)
    
    # Convert to bytes and truncate to 72 bytes if necessary
    password_bytes = password.encode('utf-8')
    if len(password_bytes) > 72:
        print("⚠️  Password is longer than 72 bytes, truncating...")
        password_bytes = password_bytes[:72]
    
    # Generate salt and hash
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    
    # Return as string
    return hashed.decode('utf-8')

# --- Main Logic ---
def create_first_admin():
    """Creates the initial admin account if one does not exist."""
    
    try:
        from app.database import SessionLocal
        db: Session = SessionLocal()
    except Exception as e:
        print(f"Error initializing database session. Ensure app.database is correctly configured. Error: {e}")
        sys.exit(1)

    print(f"Attempting to create initial admin: {FIRST_ADMIN_USERNAME}...")

    # 1. Check if admin already exists by username or email
    existing_admin = db.query(Admin).filter(
        (Admin.username == FIRST_ADMIN_USERNAME) | (Admin.email == FIRST_ADMIN_EMAIL)
    ).first()

    if existing_admin:
        print("✅ Initial admin already exists. Skipping creation.")
        db.close()
        return

    try:
        # 2. Hash the password with bcrypt directly (passlib-compatible format)
        hashed_password = create_passlib_compatible_hash(FIRST_ADMIN_PASSWORD)
        print(f"✓ Password hashed successfully using bcrypt")

        # 3. Create the new Admin model instance
        db_admin = Admin(
            username=FIRST_ADMIN_USERNAME,
            email=FIRST_ADMIN_EMAIL,
            hashed_password=hashed_password,
            first_name=FIRST_ADMIN_FIRST_NAME,
            last_name=FIRST_ADMIN_LAST_NAME,
            phone_number=FIRST_ADMIN_PHONE,
            is_active=True
        )

        # 4. Add, Commit, and Close
        db.add(db_admin)
        db.commit()
        db.refresh(db_admin)

        print(f"🎉 Successfully created initial admin: {FIRST_ADMIN_USERNAME} with ID {db_admin.id}")
        print(f"   Email: {FIRST_ADMIN_EMAIL}")
        print(f"   Phone: {FIRST_ADMIN_PHONE}")

    except Exception as e:
        db.rollback()
        print(f"❌ Failed to create initial admin: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    create_first_admin()