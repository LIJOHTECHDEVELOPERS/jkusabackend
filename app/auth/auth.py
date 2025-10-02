from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
import bcrypt  # Use bcrypt directly instead of passlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.admin import Admin
from app.schemas.user import User as UserSchema
from app.schemas.admin import Admin as AdminSchema
from app.schemas.user import Token
import os
from dotenv import load_dotenv
import logging

load_dotenv()

# Initialize logger
logger = logging.getLogger(__name__)

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

user_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="user/auth/login")
admin_oauth2_scheme = OAuth2PasswordBearer(tokenUrl="admin/auth/login")

def verify_password(plain_password, hashed_password):
    """
    Verifies a plaintext password against a hashed password using bcrypt directly.
    Handles bcrypt's 72-byte limit on the plaintext password.
    """
    try:
        # Ensure plain_password is a string
        if not isinstance(plain_password, str):
            plain_password = plain_password.decode('utf-8', 'ignore')
        
        # Ensure hashed_password is bytes
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')
        
        # Truncate password to 72 bytes if necessary
        password_bytes = plain_password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Use bcrypt to verify
        return bcrypt.checkpw(password_bytes, hashed_password)
        
    except ValueError as e:
        logger.error(f"Password verification error: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during password verification: {e}")
        return False


def get_password_hash(password):
    """
    Hashes a password using bcrypt directly.
    Ensures the password is truncated to 72 bytes before hashing.
    """
    try:
        # Ensure password is a string
        if not isinstance(password, str):
            password = str(password)
        
        # Truncate to 72 bytes if necessary
        password_bytes = password.encode('utf-8')
        if len(password_bytes) > 72:
            password_bytes = password_bytes[:72]
        
        # Generate salt and hash with bcrypt
        salt = bcrypt.gensalt(rounds=12)
        hashed = bcrypt.hashpw(password_bytes, salt)
        
        # Return as string
        return hashed.decode('utf-8')
        
    except Exception as e:
        logger.error(f"Error hashing password: {e}")
        raise


def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_admin(db: Session, username: str):
    return db.query(Admin).filter(Admin.username == username).first()

def get_admin_by_identifier(db: Session, identifier: str):
    """Get admin by username or email"""
    return db.query(Admin).filter(
        (Admin.username == identifier) | (Admin.email == identifier)
    ).first()

def get_admin_by_username(db: Session, username: str):
    """Get admin by username only"""
    return db.query(Admin).filter(Admin.username == username).first()

def get_admin_by_email(db: Session, email: str):
    """Get admin by email only"""
    return db.query(Admin).filter(Admin.email == email).first()

def get_user_by_identifier(db: Session, identifier: str):
    """Get user by username or email"""
    return db.query(User).filter(
        (User.username == identifier) | (User.email == identifier)
    ).first()

def get_user_by_username(db: Session, username: str):
    """Get user by username only"""
    return db.query(User).filter(User.username == username).first()

def get_user_by_email(db: Session, email: str):
    """Get user by email only"""
    return db.query(User).filter(User.email == email).first()

async def get_current_user(token: str = Depends(user_oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate user credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_type: str = payload.get("type")
        if username is None or user_type != "user":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = get_user(db, username=username)
    if user is None:
        raise credentials_exception
    return UserSchema(id=user.id, username=user.username)

async def get_current_admin(token: str = Depends(admin_oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate admin credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_type: str = payload.get("type")
        if username is None or user_type != "admin":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    admin = get_admin(db, username=username)
    if admin is None:
        raise credentials_exception
    return AdminSchema(id=admin.id, username=admin.username)