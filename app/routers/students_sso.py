from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from app.database import get_db
from app.models import College, School, student # Ensure 'student' is the SQLAlchemy model name
from app.schemas import studentCreate, studentLogin, studentResponse, TokenData
import uuid
import os
import smtplib
from email.mime.text import MIMEText
import logging

logger = logging.getLogger(__name__)

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key")  # Replace with secure key in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30
COOKIE_NAME = "access_token"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = os.getenv("EMAIL_PORT", 587)
EMAIL_STUDENT = os.getenv("EMAIL_STUDENT", "your-email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your-email-password")

# Initialize password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# Router
auth_router = APIRouter(prefix="/auth", tags=["auth"])

# Helper Functions
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hash."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Generates a hash for a given password."""
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def send_verification_email(email: str, token: str):
    """Sends an email verification link to the student."""
    # NOTE: Replace 'http://your-domain.com' with the actual domain of your frontend
    verification_url = f"http://your-domain.com/auth/verify?token={token}"
    msg = MIMEText(f"Please verify your email by clicking the link: {verification_url}")
    msg['Subject'] = 'Verify Your Email - JKUAT Student Association'
    msg['From'] = EMAIL_STUDENT
    msg['To'] = email

    try:
        # NOTE: Ensure EMAIL_STUDENT and EMAIL_PASSWORD environment variables are set correctly.
        with smtplib.SMTP(EMAIL_HOST, int(EMAIL_PORT)) as server:
            server.starttls()
            server.login(EMAIL_STUDENT, EMAIL_PASSWORD)
            server.send_message(msg)
        logger.info(f"Verification email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send verification email to {email}: {str(e)}")
        # Raise HTTP 500 but still commit the user creation in register_student
        # to allow them to manually retry verification if necessary, 
        # but for simplicity here, we re-raise the exception.
        raise HTTPException(status_code=500, detail="Failed to send verification email. Please contact support.")

async def get_current_student(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> student:
    """Dependency to get the current authenticated student object."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        student_id: int = payload.get("student_id")
        email: str = payload.get("email")
        if student_id is None or email is None:
            raise credentials_exception
        token_data = TokenData(student_id=student_id, email=email)
    except JWTError:
        raise credentials_exception

    # FIX: Use the lowercase 'student' model imported from app.models
    db_student = db.query(student).filter(
        student.id == token_data.student_id, 
        student.email == token_data.email
    ).first()
    
    # FIX: Check against the local variable db_student
    if db_student is None or not db_student.is_active:
        raise credentials_exception
        
    return db_student

# Predefined Colleges and Schools
COLLEGES_SCHOOLS = {
    "COHES": [
        "School of Nursing",
        "School of Medicine",
        "School of Pharmacy",
        "School of Public Health",
        "School of Biomedical Sciences"
    ],
    "COETEC": [
        "School of Architecture and Building Sciences (SABS)",
        "School of Mechanical, Manufacturing & Materials Engineering (SoMMME)",
        "School of Electrical, Electronic and Information Engineering (SEEIE)",
        "School of Civil, Environmental and Geospatial Engineering (SCEGE)",
        "School of Biosystems and Environmental Engineering (SoBEE)"
    ],
    "COPAS": [
        "School of Biological Sciences",
        "School of Mathematical and Physical Sciences",
        "School of Computing and Information Technology"
    ],
    "COANRE": [
        "School of Agriculture and Environmental Sciences (SOAES)",
        "School of Food and Nutrition Sciences (SOFNUS)",
        "School of Natural Resources and Animal Sciences (SONRAS)"
    ],
    "COHRED": [
        "School of Business",
        "School of Entrepreneurship, Procurement and Management",
        "School of Communication and Development Studies"
    ]
}

def populate_colleges_schools(db: Session):
    """Initializes colleges and schools in the database based on the predefined list."""
    for college_name, schools in COLLEGES_SCHOOLS.items():
        college = db.query(College).filter(College.name == college_name).first()
        if not college:
            college = College(name=college_name)
            db.add(college)
            db.commit()
            db.refresh(college)
        for school_name in schools:
            school = db.query(School).filter(School.name == school_name, School.college_id == college.id).first()
            if not school:
                school = School(name=school_name, college_id=college.id)
                db.add(school)
        db.commit()

# Routes
@auth_router.post("/register")
async def register_student(
    # FIX: Renamed input variable to student_data to avoid shadowing the SQLAlchemy model 'student'
    student_data: studentCreate,
    db: Session = Depends(get_db)
):
    """Registers a new student and sends a verification email."""
    # Initialize colleges and schools if not already populated
    populate_colleges_schools(db)

    # Validate college and school IDs against the data
    college = db.query(College).filter(College.id == student_data.college_id).first()
    if not college:
        raise HTTPException(status_code=400, detail="Invalid college ID")
    school = db.query(School).filter(School.id == student_data.school_id, School.college_id == student_data.college_id).first()
    if not school:
        raise HTTPException(status_code=400, detail="Invalid school ID or school does not belong to the selected college")

    # Validate year of study
    if student_data.year_of_study < 1 or student_data.year_of_study > 6:
        raise HTTPException(status_code=400, detail="Year of study must be between 1 and 6")

    # Check for existing email or registration number
    # FIX: Compare student model fields against student_data fields, ensuring case consistency
    if db.query(student).filter(student.email == student_data.email.lower()).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    if db.query(student).filter(student.registration_number == student_data.registration_number.upper()).first():
        raise HTTPException(status_code=400, detail="Registration number already registered")

    # Create student
    verification_token = str(uuid.uuid4())
    db_student = student(
        first_name=student_data.first_name.strip(),
        last_name=student_data.last_name.strip(),
        email=student_data.email.lower(), # Store email in lowercase
        phone_number=student_data.phone_number,
        registration_number=student_data.registration_number.upper(), # Store registration number in uppercase
        college_id=student_data.college_id,
        school_id=student_data.school_id,
        course=student_data.course.strip(),
        year_of_study=student_data.year_of_study,
        hashed_password=get_password_hash(student_data.password),
        verification_token=verification_token
    )
    db.add(db_student)
    db.commit()
    db.refresh(db_student)

    # Send verification email
    send_verification_email(student_data.email, verification_token)

    return {"detail": "Student registered successfully. Please check your email for verification link."}

@auth_router.get("/verify")
async def verify_email(token: str, db: Session = Depends(get_db)):
    """Verifies a student's email using the token provided in the link."""
    db_student = db.query(student).filter(student.verification_token == token).first()
    if not db_student:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")
    
    db_student.is_active = True
    db_student.verification_token = None
    db.commit()
    return {"detail": "Email verified successfully. You can now log in."}

@auth_router.post("/login")
async def login_student(
    response: Response,
    login_data: studentLogin,
    db: Session = Depends(get_db)
):
    """Authenticates a student via email/registration number and password, setting an HTTP-only cookie."""
    
    # Attempt to find the student using either lowercase email or uppercase registration number
    db_student = db.query(student).filter(
        (student.email == login_data.login_id.lower()) | 
        (student.registration_number == login_data.login_id.upper())
    ).first()

    if not db_student or not verify_password(login_data.password, db_student.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/registration number or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not db_student.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not verified. Please check your email for verification link."
        )

    # Create and set the access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"student_id": db_student.id, "email": db_student.email},
        expires_delta=access_token_expires
    )
    
    # Set HTTP-only cookie
    response.set_cookie(
        key=COOKIE_NAME,
        value=access_token,
        httponly=True,
        secure=True,  # IMPORTANT: Should be True in production with HTTPS
        samesite="lax",
        max_age=int(access_token_expires.total_seconds())
    )
    
    return {"detail": "Login successful", "student": studentResponse.from_orm(db_student)}

@auth_router.post("/logout")
async def logout_student(response: Response):
    """Deletes the authentication cookie to log the student out."""
    response.delete_cookie(COOKIE_NAME)
    return {"detail": "Logout successful"}

@auth_router.get("/me", response_model=studentResponse)
async def get_current_student_details(current_student: student = Depends(get_current_student)):
    """Returns the details of the currently authenticated student."""
    return current_student
