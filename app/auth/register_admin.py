from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.admin import Admin
from app.schemas.admin import AdminCreate, Token
from app.auth.auth import verify_password, get_password_hash, create_access_token, get_admin, get_current_admin

router = APIRouter(prefix="/admin/auth", tags=["admin_auth"])

@router.post("/register-admin", response_model=Token)
def register_admin(admin: AdminCreate, db: Session = Depends(get_db), current_admin=Depends(get_current_admin)):
    # Check if username already exists
    db_admin = get_admin(db, username=admin.username)
    if db_admin:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Check if email already exists (if you have email field)
    if hasattr(admin, 'email') and admin.email:
        existing_admin = db.query(Admin).filter(Admin.email == admin.email).first()
        if existing_admin:
            raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password
    hashed_password = get_password_hash(admin.password)
    
    # Create new admin with all fields
    db_admin = Admin(
        first_name=admin.first_name,
        last_name=admin.last_name,
        email=admin.email,
        phone_number=admin.phone_number,
        username=admin.username,
        hashed_password=hashed_password
    )
    
    db.add(db_admin)
    db.commit()
    db.refresh(db_admin)
    
    access_token = create_access_token(data={"sub": admin.username, "type": "admin"})
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    admin = get_admin(db, username=form_data.username)
    if not admin or not verify_password(form_data.password, admin.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": admin.username, "type": "admin"})
    return {"access_token": access_token, "token_type": "bearer"}