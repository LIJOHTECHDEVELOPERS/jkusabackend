from fastapi import APIRouter, Depends, HTTPException, Response, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import bcrypt
from datetime import datetime, timedelta
from typing import Optional
import uuid
import os
import logging
import re
from collections import defaultdict
from threading import Lock

# Import models, schemas, and database
from app.database import get_db
from app.models.student import College, School, student
from app.schemas.student import (
    studentCreate, 
    studentLogin, 
    studentResponse, 
    TokenData,
    PasswordResetRequest,
    PasswordResetConfirm
)

# Import email service
from app.services.email_service import (
    send_verification_email, 
    send_welcome_email,
    send_password_reset_email
)

logger = logging.getLogger(__name__)

# ==================== CONFIGURATION ====================
SECRET_KEY = os.getenv("JWT_SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "your-secret-key":
    raise ValueError("JWT_SECRET_KEY must be set to a strong random value in production!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
VERIFICATION_TOKEN_EXPIRE_HOURS = 24
PASSWORD_RESET_TOKEN_EXPIRE_HOURS = 1

COOKIE_NAME = "access_token"
REFRESH_COOKIE_NAME = "refresh_token"

# Security settings
MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "5"))
LOCKOUT_DURATION_MINUTES = int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))

# Environment check
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/students/auth/login")

# ==================== ROUTER INSTANCE ====================
router = APIRouter(prefix="/students/auth", tags=["Authentication & SSO"])

# ==================== RATE LIMITING & SECURITY ====================

class RateLimiter:
    """Simple in-memory rate limiter (use Redis in production for distributed systems)"""
    def __init__(self):
        self.requests = defaultdict(list)
        self.lock = Lock()
    
    def is_allowed(self, identifier: str, max_requests: int, window_seconds: int) -> bool:
        with self.lock:
            now = datetime.utcnow()
            cutoff = now - timedelta(seconds=window_seconds)
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if req_time > cutoff
            ]
            if len(self.requests[identifier]) >= max_requests:
                return False
            self.requests[identifier].append(now)
            return True

class LoginAttemptTracker:
    """Track failed login attempts (use Redis in production)"""
    def __init__(self):
        self.attempts = defaultdict(lambda: {"count": 0, "locked_until": None})
        self.lock = Lock()
    
    def record_failed_attempt(self, identifier: str):
        with self.lock:
            self.attempts[identifier]["count"] += 1
            if self.attempts[identifier]["count"] >= MAX_LOGIN_ATTEMPTS:
                self.attempts[identifier]["locked_until"] = (
                    datetime.utcnow() + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
                )
                logger.warning(f"Account locked due to failed attempts: {identifier}")
    
    def is_locked(self, identifier: str) -> tuple[bool, Optional[datetime]]:
        with self.lock:
            locked_until = self.attempts[identifier]["locked_until"]
            if locked_until and locked_until > datetime.utcnow():
                return True, locked_until
            if locked_until:
                self.attempts[identifier] = {"count": 0, "locked_until": None}
            return False, None
    
    def reset_attempts(self, identifier: str):
        with self.lock:
            self.attempts[identifier] = {"count": 0, "locked_until": None}
    
    def get_remaining_attempts(self, identifier: str) -> int:
        with self.lock:
            return MAX_LOGIN_ATTEMPTS - self.attempts[identifier]["count"]

# Initialize security components
rate_limiter = RateLimiter()
login_tracker = LoginAttemptTracker()

# ==================== PASSWORD VALIDATION ====================

def validate_password_strength(password: str) -> tuple[bool, str]:
    """
    Validate password meets security requirements.
    Returns (is_valid, error_message)
    """
    if not password:
        return False, "Password cannot be empty"
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    if len(password) > 128:
        return False, "Password must not exceed 128 characters"
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"
    if not re.search(r"\d", password):
        return False, "Password must contain at least one number"
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Password must contain at least one special character (!@#$%^&*(),.?\":{}|<>)"
    common_passwords = ["password", "12345678", "qwerty", "admin", "letmein"]
    if password.lower() in common_passwords:
        return False, "Password is too common. Please choose a stronger password"
    return True, ""

# ==================== HELPER FUNCTIONS ====================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hash."""
    try:
        password_bytes = plain_password.encode('utf-8')[:72]
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hashed_bytes)
    except Exception as e:
        logger.error(f"Password verification error: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """Generates a hash for a given password."""
    password_bytes = password.encode('utf-8')[:72]
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Creates a JWT access token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "type": "access"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def create_refresh_token(data: dict) -> str:
    """Creates a JWT refresh token."""
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def sanitize_input(input_str: str) -> str:
    """Sanitize user input to prevent injection attacks."""
    if not input_str:
        return ""
    sanitized = input_str.replace('\x00', '').strip()
    return sanitized

def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    return request.client.host if request.client else "unknown"

def validate_token_expiry(token_expiry: datetime, email: str) -> None:
    """Validate token expiry with consistent timezone handling."""
    current_time = datetime.utcnow()
    if token_expiry.tzinfo is None:
        if token_expiry < current_time:
            logger.warning(f"Expired token for: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "The link has expired. Please request a new one.",
                    "code": "TOKEN_EXPIRED"
                }
            )
    else:
        from datetime import timezone
        current_time_aware = current_time.replace(tzinfo=timezone.utc)
        if token_expiry < current_time_aware:
            logger.warning(f"Expired token for: {email}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "The link has expired. Please request a new one.",
                    "code": "TOKEN_EXPIRED"
                }
            )

async def get_current_student(
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
) -> student:
    """Dependency to get the current authenticated student object."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "success": False,
            "message": "Could not validate credentials. Please sign in again.",
            "code": "INVALID_CREDENTIALS"
        },
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "access":
            raise credentials_exception
        student_id: int = payload.get("student_id")
        email: str = payload.get("email")
        if student_id is None or email is None:
            raise credentials_exception
        token_data = TokenData(student_id=student_id, email=email)
    except JWTError as e:
        logger.warning(f"JWT validation failed: {str(e)}")
        raise credentials_exception

    db_student = db.query(student).filter(
        student.id == token_data.student_id, 
        student.email == token_data.email
    ).first()
    
    if db_student is None:
        logger.warning(f"Student not found: {token_data.student_id}")
        raise credentials_exception
    
    if not db_student.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "success": False,
                "message": "Account not verified. Please check your email for the verification link.",
                "code": "EMAIL_NOT_VERIFIED"
            }
        )
        
    return db_student

# ==================== DATA POPULATION ====================

COLLEGES_SCHOOLS = {
    "COHES": [
        "School of Nursing", "School of Medicine", "School of Pharmacy",
        "School of Public Health", "School of Biomedical Sciences"
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
    """Initializes colleges and schools in the database."""
    try:
        for college_name, schools in COLLEGES_SCHOOLS.items():
            college = db.query(College).filter(College.name == college_name).first()
            if not college:
                college = College(name=college_name)
                db.add(college)
                db.commit()
                db.refresh(college)
            
            for school_name in schools:
                school = db.query(School).filter(
                    School.name == school_name, 
                    School.college_id == college.id
                ).first()
                if not school:
                    school = School(name=school_name, college_id=college.id)
                    db.add(school)
                    db.commit()
        db.commit()
    except Exception as e:
        logger.error(f"Error populating colleges/schools: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred while initializing data",
                "code": "SERVER_ERROR"
            }
        )

# ==================== ROUTES ====================

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_student_route(
    request: Request,
    student_data: studentCreate,
    db: Session = Depends(get_db)
):
    """Registers a new student with comprehensive validation and security checks."""
    client_ip = get_client_ip(request)
    if not rate_limiter.is_allowed(
        f"register:{client_ip}", 
        RATE_LIMIT_REQUESTS, 
        RATE_LIMIT_WINDOW_SECONDS
    ):
        logger.warning(f"Rate limit exceeded for registration from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "message": "Too many registration attempts. Please wait a minute and try again.",
                "code": "RATE_LIMIT_EXCEEDED"
            }
        )
    
    try:
        populate_colleges_schools(db)

        # Input sanitization
        student_data.first_name = sanitize_input(student_data.first_name)
        student_data.last_name = sanitize_input(student_data.last_name)
        student_data.email = sanitize_input(student_data.email)
        student_data.course = sanitize_input(student_data.course)
        student_data.registration_number = sanitize_input(student_data.registration_number)
        student_data.phone_number = sanitize_input(student_data.phone_number) if student_data.phone_number else None

        # Validate required fields
        if not all([student_data.first_name, student_data.last_name, student_data.email, 
                   student_data.registration_number, student_data.course]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "All required fields must be provided",
                    "code": "MISSING_FIELDS"
                }
            )

        # Validate password strength
        is_valid, error_msg = validate_password_strength(student_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": error_msg,
                    "code": "WEAK_PASSWORD"
                }
            )

        # Validate email format
        email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_regex, student_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Please enter a valid email address",
                    "code": "INVALID_EMAIL"
                }
            )

        # Validate phone number format if provided
        if student_data.phone_number:
            phone_regex = r'^\+?1?\d{9,15}$'
            if not re.match(phone_regex, student_data.phone_number):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Invalid phone number format",
                        "code": "INVALID_PHONE"
                    }
                )

        # Validate college and school IDs
        college = db.query(College).filter(College.id == student_data.college_id).first()
        if not college:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Please select a valid college",
                    "code": "INVALID_COLLEGE"
                }
            )
        
        school = db.query(School).filter(
            School.id == student_data.school_id, 
            School.college_id == student_data.college_id
        ).first()
        if not school:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Please select a valid school that belongs to your college",
                    "code": "INVALID_SCHOOL"
                }
            )

        # Validate year of study
        if student_data.year_of_study < 1 or student_data.year_of_study > 6:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Year of study must be between 1 and 6",
                    "code": "INVALID_YEAR"
                }
            )

        # Check for existing email or registration number
        email_lower = student_data.email.lower()
        reg_number_upper = student_data.registration_number.upper()
        
        existing_student = db.query(student).filter(
            (student.email == email_lower) | 
            (student.registration_number == reg_number_upper)
        ).first()
        
        if existing_student:
            if existing_student.email == email_lower:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "success": False,
                        "message": "This email is already registered. Please sign in or use a different email.",
                        "code": "EMAIL_EXISTS"
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "success": False,
                        "message": "This registration number is already in use. Please contact support.",
                        "code": "REG_NUMBER_EXISTS"
                    }
                )

        # Create student
        verification_token = str(uuid.uuid4())
        token_expiry = datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
        
        db_student = student(
            first_name=student_data.first_name.strip(),
            last_name=student_data.last_name.strip(),
            email=email_lower,
            phone_number=student_data.phone_number,
            registration_number=reg_number_upper,
            college_id=student_data.college_id,
            school_id=student_data.school_id,
            course=student_data.course.strip(),
            year_of_study=student_data.year_of_study,
            hashed_password=get_password_hash(student_data.password),
            verification_token=verification_token,
            verification_token_expiry=token_expiry,
            is_active=False,
            created_at=datetime.utcnow()
        )
        
        db.add(db_student)
        db.commit()
        db.refresh(db_student)
        
        logger.info(f"New student registered: {db_student.email} (ID: {db_student.id})")

        # Send verification email
        try:
            user_name = f"{db_student.first_name} {db_student.last_name}"
            success = send_verification_email(
                email=db_student.email,
                user_name=user_name,
                token=verification_token
            )
            
            return {
                "success": True,
                "message": "Registration successful! Please check your email to verify your account.",
                "email": db_student.email,
                "email_sent": success,
                "code": "REGISTRATION_SUCCESS"
            }
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
            return {
                "success": True,
                "message": "Registration successful, but we couldn't send the verification email. Please contact support.",
                "email": db_student.email,
                "email_sent": False,
                "code": "EMAIL_SEND_FAILED"
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred during registration. Please try again.",
                "code": "SERVER_ERROR"
            }
        )

@router.get("/verify")
async def verify_email_route(token: str, db: Session = Depends(get_db)):
    """Verifies a student's email using the token provided in the link."""
    try:
        token = sanitize_input(token)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Verification token is required",
                    "code": "MISSING_TOKEN"
                }
            )
        
        db_student = db.query(student).filter(
            student.verification_token == token
        ).first()
        
        if not db_student:
            logger.warning(f"Invalid verification token attempted: {token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Invalid verification link. Please request a new verification email.",
                    "code": "INVALID_TOKEN"
                }
            )
        
        # Check token expiry
        if db_student.verification_token_expiry:
            validate_token_expiry(db_student.verification_token_expiry, db_student.email)
        
        if db_student.is_active:
            return {
                "success": True,
                "message": "Your email is already verified. You can sign in now.",
                "code": "ALREADY_VERIFIED",
                "already_verified": True
            }
        
        db_student.is_active = True
        db_student.verification_token = None
        db_student.verification_token_expiry = None
        db_student.email_verified_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Email verified successfully: {db_student.email}")
        
        try:
            user_name = f"{db_student.first_name} {db_student.last_name}"
            send_welcome_email(
                email=db_student.email,
                user_name=user_name
            )
        except Exception as e:
            logger.error(f"Failed to send welcome email: {str(e)}")
        
        return {
            "success": True,
            "message": f"Welcome, {db_student.first_name}! Your email has been verified successfully.",
            "code": "VERIFICATION_SUCCESS",
            "verified": True,
            "student_name": f"{db_student.first_name} {db_student.last_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred during verification. Please try again.",
                "code": "SERVER_ERROR"
            }
        )

@router.post("/resend-verification")
async def resend_verification_route(
    request: Request,
    email: str,
    db: Session = Depends(get_db)
):
    """Resend verification email to a student."""
    client_ip = get_client_ip(request)
    if not rate_limiter.is_allowed(
        f"resend:{client_ip}", 
        3,
        300
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "message": "Too many requests. Please wait a few minutes before trying again.",
                "code": "RATE_LIMIT_EXCEEDED"
            }
        )
    
    try:
        email = sanitize_input(email).lower()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Email address is required",
                    "code": "MISSING_EMAIL"
                }
            )
        
        db_student = db.query(student).filter(student.email == email).first()
        
        if not db_student:
            return {
                "success": True,
                "message": "If this email is registered, a verification link has been sent.",
                "code": "EMAIL_SENT"
            }
        
        if db_student.is_active:
            return {
                "success": True,
                "message": "This account is already verified. You can sign in now.",
                "code": "ALREADY_VERIFIED"
            }
        
        verification_token = str(uuid.uuid4())
        token_expiry = datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
        
        db_student.verification_token = verification_token
        db_student.verification_token_expiry = token_expiry
        db.commit()
        
        email_sent = False
        try:
            user_name = f"{db_student.first_name} {db_student.last_name}"
            email_sent = send_verification_email(
                email=db_student.email,
                user_name=user_name,
                token=verification_token
            )
            logger.info(f"Verification email {'sent' if email_sent else 'failed'} to: {email}")
        except Exception as e:
            logger.error(f"Failed to send verification email: {str(e)}")
        
        return {
            "success": True,
            "message": "Verification email sent! Please check your inbox and spam folder.",
            "code": "EMAIL_SENT",
            "email_sent": email_sent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resending verification: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred. Please try again later.",
                "code": "SERVER_ERROR"
            }
        )

@router.post("/login")
async def login_student_route(
    request: Request,
    response: Response,
    login_data: studentLogin,
    db: Session = Depends(get_db)
):
    """Authenticates a student with enhanced error handling and auto-verification flow."""
    login_id = sanitize_input(login_data.login_id)
    client_ip = get_client_ip(request)
    
    if not login_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "message": "Email or registration number is required",
                "code": "MISSING_LOGIN_ID"
            }
        )
    
    if not rate_limiter.is_allowed(
        f"login:{client_ip}", 
        RATE_LIMIT_REQUESTS, 
        RATE_LIMIT_WINDOW_SECONDS
    ):
        logger.warning(f"Rate limit exceeded for login from IP: {client_ip}")
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "message": "Too many login attempts. Please wait a minute and try again.",
                "code": "RATE_LIMIT_EXCEEDED"
            }
        )
    
    is_locked, locked_until = login_tracker.is_locked(login_id)
    if is_locked:
        minutes_remaining = int((locked_until - datetime.utcnow()).total_seconds() / 60) + 1
        logger.warning(f"Login attempt on locked account: {login_id}")
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail={
                "success": False,
                "message": f"Your account has been temporarily locked for security. Please try again in {minutes_remaining} minute{'s' if minutes_remaining != 1 else ''}.",
                "code": "ACCOUNT_LOCKED",
                "locked_until": locked_until.isoformat(),
                "minutes_remaining": minutes_remaining
            }
        )
    
    try:
        db_student = db.query(student).filter(
            (student.email == login_id.lower()) | 
            (student.registration_number == login_id.upper())
        ).first()

        if not db_student or not verify_password(login_data.password, db_student.hashed_password):
            login_tracker.record_failed_attempt(login_id)
            remaining = login_tracker.get_remaining_attempts(login_id)
            
            logger.warning(f"Failed login attempt for: {login_id} from IP: {client_ip}")
            
            if remaining > 0:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail={
                        "success": False,
                        "message": f"Invalid email/registration number or password. {remaining} attempt{'s' if remaining != 1 else ''} remaining.",
                        "code": "INVALID_CREDENTIALS",
                        "attempts_remaining": remaining
                    }
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail={
                        "success": False,
                        "message": f"Account locked due to multiple failed login attempts. Please try again in {LOCKOUT_DURATION_MINUTES} minutes.",
                        "code": "ACCOUNT_LOCKED",
                        "minutes_remaining": LOCKOUT_DURATION_MINUTES
                    }
                )
        
        if not db_student.is_active:
            logger.info(f"Login attempt on unverified account: {db_student.email}")
            
            needs_new_token = (
                not db_student.verification_token or
                not db_student.verification_token_expiry or
                db_student.verification_token_expiry < datetime.utcnow()
            )
            
            if needs_new_token:
                verification_token = str(uuid.uuid4())
                token_expiry = datetime.utcnow() + timedelta(hours=VERIFICATION_TOKEN_EXPIRE_HOURS)
                db_student.verification_token = verification_token
                db_student.verification_token_expiry = token_expiry
                db.commit()
            else:
                verification_token = db_student.verification_token
            
            email_sent = False
            try:
                user_name = f"{db_student.first_name} {db_student.last_name}"
                email_sent = send_verification_email(
                    email=db_student.email,
                    user_name=user_name,
                    token=verification_token
                )
                logger.info(f"Verification email {'sent' if email_sent else 'failed'} to: {db_student.email}")
            except Exception as e:
                logger.error(f"Failed to send verification email: {str(e)}")
            
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "success": False,
                    "message": "Your email is not verified yet. We've sent a verification link to your email.",
                    "code": "EMAIL_NOT_VERIFIED",
                    "email": db_student.email,
                    "email_sent": email_sent,
                    "requires_verification": True,
                    "student_name": f"{db_student.first_name} {db_student.last_name}"
                }
            )
        
        login_tracker.reset_attempts(login_id)
        db_student.last_login = datetime.utcnow()
        db.commit()
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"student_id": db_student.id, "email": db_student.email},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"student_id": db_student.id, "email": db_student.email}
        )
        
        response.set_cookie(
            key=COOKIE_NAME,
            value=access_token,
            httponly=True,
            secure=IS_PRODUCTION,
            samesite="lax",
            max_age=int(access_token_expires.total_seconds())
        )
        
        response.set_cookie(
            key=REFRESH_COOKIE_NAME,
            value=refresh_token,
            httponly=True,
            secure=IS_PRODUCTION,
            samesite="lax",
            max_age=int(timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS).total_seconds())
        )
        
        logger.info(f"Successful login: {db_student.email} from IP: {client_ip}")
        
        return {
            "success": True,
            "message": f"Welcome back, {db_student.first_name}!",
            "code": "LOGIN_SUCCESS",
            "student": studentResponse.from_orm(db_student),
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An unexpected error occurred during login. Please try again.",
                "code": "SERVER_ERROR"
            }
        )

@router.post("/refresh")
async def refresh_token_route(
    request: Request,
    response: Response,
    db: Session = Depends(get_db)
):
    """Refresh access token using refresh token."""
    refresh_token = request.cookies.get(REFRESH_COOKIE_NAME)
    
    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Session expired. Please sign in again.",
                "code": "NO_REFRESH_TOKEN"
            }
        )
    
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Invalid session. Please sign in again.",
                    "code": "INVALID_TOKEN_TYPE"
                }
            )
        
        student_id: int = payload.get("student_id")
        email: str = payload.get("email")
        
        if student_id is None or email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Invalid session. Please sign in again.",
                    "code": "INVALID_TOKEN"
                }
            )
        
        db_student = db.query(student).filter(
            student.id == student_id,
            student.email == email,
            student.is_active == True
        ).first()
        
        if not db_student:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Account not found or inactive. Please sign in again.",
                    "code": "STUDENT_NOT_FOUND"
                }
            )
        
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"student_id": db_student.id, "email": db_student.email},
            expires_delta=access_token_expires
        )
        
        response.set_cookie(
            key=COOKIE_NAME,
            value=access_token,
            httponly=True,
            secure=IS_PRODUCTION,
            samesite="lax",
            max_age=int(access_token_expires.total_seconds())
        )
        
        logger.info(f"Token refreshed for: {db_student.email}")
        
        return {
            "success": True,
            "message": "Session refreshed successfully",
            "code": "TOKEN_REFRESHED",
            "access_token": access_token,
            "token_type": "bearer"
        }
        
    except JWTError as e:
        logger.warning(f"Invalid refresh token: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "success": False,
                "message": "Your session has expired. Please sign in again.",
                "code": "TOKEN_EXPIRED"
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred while refreshing your session",
                "code": "SERVER_ERROR"
            }
        )

@router.post("/logout")
async def logout_student_route(
    response: Response,
    current_student: student = Depends(get_current_student)
):
    """Logs out the student by deleting authentication cookies."""
    response.delete_cookie(COOKIE_NAME)
    response.delete_cookie(REFRESH_COOKIE_NAME)
    
    logger.info(f"Student logged out: {current_student.email}")
    
    return {
        "success": True,
        "message": "You have been logged out successfully",
        "code": "LOGOUT_SUCCESS"
    }

@router.get("/me", response_model=studentResponse)
async def get_current_student_details_route(
    current_student: student = Depends(get_current_student)
):
    """Returns the details of the currently authenticated student."""
    return {
        "success": True,
        "message": "User details retrieved successfully",
        "code": "USER_DETAILS_RETRIEVED",
        "data": studentResponse.from_orm(current_student)
    }

@router.post("/password-reset-request")
async def request_password_reset_route(
    request: Request,
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_db)
):
    """Request a password reset email."""
    client_ip = get_client_ip(request)
    if not rate_limiter.is_allowed(
        f"reset:{client_ip}", 
        3,
        300
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "message": "Too many password reset requests. Please wait a few minutes.",
                "code": "RATE_LIMIT_EXCEEDED"
            }
        )
    
    try:
        email = sanitize_input(reset_request.email).lower()
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Email address is required",
                    "code": "MISSING_EMAIL"
                }
            )
        
        db_student = db.query(student).filter(student.email == email).first()
        
        if not db_student:
            logger.warning(f"Password reset requested for non-existent email: {email}")
            return {
                "success": True,
                "message": "If this email is registered, a password reset link has been sent.",
                "code": "EMAIL_SENT"
            }
        
        reset_token = str(uuid.uuid4())
        token_expiry = datetime.utcnow() + timedelta(hours=PASSWORD_RESET_TOKEN_EXPIRE_HOURS)
        
        db_student.password_reset_token = reset_token
        db_student.password_reset_token_expiry = token_expiry
        db.commit()
        
        email_sent = False
        try:
            user_name = f"{db_student.first_name} {db_student.last_name}"
            email_sent = send_password_reset_email(
                email=db_student.email,
                user_name=user_name,
                token=reset_token
            )
            logger.info(f"Password reset email {'sent' if email_sent else 'failed'} to: {email}")
        except Exception as e:
            logger.error(f"Error sending password reset email: {str(e)}")
        
        return {
            "success": True,
            "message": "Password reset link sent! Please check your inbox and spam folder.",
            "code": "EMAIL_SENT",
            "email_sent": email_sent
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred. Please try again later.",
                "code": "SERVER_ERROR"
            }
        )

@router.post("/password-reset-confirm")
async def confirm_password_reset_route(
    request: Request,
    reset_confirm: PasswordResetConfirm,
    db: Session = Depends(get_db)
):
    """Confirm password reset with token and new password."""
    client_ip = get_client_ip(request)
    if not rate_limiter.is_allowed(
        f"reset-confirm:{client_ip}", 
        5,
        300
    ):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "success": False,
                "message": "Too many attempts. Please try again in a few minutes.",
                "code": "RATE_LIMIT_EXCEEDED"
            }
        )
    
    try:
        token = sanitize_input(reset_confirm.token)
        if not token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Reset token is required",
                    "code": "MISSING_TOKEN"
                }
            )
        
        db_student = db.query(student).filter(
            student.password_reset_token == token
        ).first()
        
        if not db_student:
            logger.warning(f"Invalid password reset token attempted: {token[:10]}...")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Invalid or expired reset link. Please request a new password reset.",
                    "code": "INVALID_TOKEN"
                }
            )
        
        if db_student.password_reset_token_expiry:
            validate_token_expiry(db_student.password_reset_token_expiry, db_student.email)
        
        is_valid, error_msg = validate_password_strength(reset_confirm.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": error_msg,
                    "code": "WEAK_PASSWORD"
                }
            )
        
        if reset_confirm.new_password != reset_confirm.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "Passwords do not match. Please try again.",
                    "code": "PASSWORD_MISMATCH"
                }
            )
        
        if verify_password(reset_confirm.new_password, db_student.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "New password must be different from current password",
                    "code": "SAME_PASSWORD"
                }
            )
        
        db_student.hashed_password = get_password_hash(reset_confirm.new_password)
        db_student.password_reset_token = None
        db_student.password_reset_token_expiry = None
        db_student.password_changed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Password reset successful for: {db_student.email}")
        
        return {
            "success": True,
            "message": "Password reset successful! You can now sign in with your new password.",
            "code": "PASSWORD_RESET_SUCCESS"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password reset confirmation error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred. Please try again later.",
                "code": "SERVER_ERROR"
            }
        )

@router.post("/change-password")
async def change_password_route(
    old_password: str,
    new_password: str,
    confirm_password: str,
    current_student: student = Depends(get_current_student),
    db: Session = Depends(get_db)
):
    """Change password for authenticated user."""
    try:
        old_password = sanitize_input(old_password)
        new_password = sanitize_input(new_password)
        confirm_password = sanitize_input(confirm_password)
        
        if not all([old_password, new_password, confirm_password]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "All password fields are required",
                    "code": "MISSING_FIELDS"
                }
            )
        
        if not verify_password(old_password, current_student.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "success": False,
                    "message": "Current password is incorrect",
                    "code": "INCORRECT_PASSWORD"
                }
            )
        
        is_valid, error_msg = validate_password_strength(new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": error_msg,
                    "code": "WEAK_PASSWORD"
                }
            )
        
        if new_password != confirm_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "New passwords do not match",
                    "code": "PASSWORD_MISMATCH"
                }
            )
        
        if verify_password(new_password, current_student.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "message": "New password must be different from current password",
                    "code": "SAME_PASSWORD"
                }
            )
        
        current_student.hashed_password = get_password_hash(new_password)
        current_student.password_changed_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Password changed for: {current_student.email}")
        
        return {
            "success": True,
            "message": "Password changed successfully",
            "code": "PASSWORD_CHANGED"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred. Please try again later.",
                "code": "SERVER_ERROR"
            }
        )

@router.get("/colleges")
async def get_colleges_route(db: Session = Depends(get_db)):
    """Get all colleges."""
    try:
        populate_colleges_schools(db)
        colleges = db.query(College).all()
        return {
            "success": True,
            "message": "Colleges retrieved successfully",
            "code": "COLLEGES_RETRIEVED",
            "data": [{"id": c.id, "name": c.name} for c in colleges]
        }
    except Exception as e:
        logger.error(f"Error fetching colleges: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred while fetching colleges",
                "code": "SERVER_ERROR"
            }
        )

@router.get("/colleges/{college_id}/schools")
async def get_schools_route(college_id: int, db: Session = Depends(get_db)):
    """Get all schools in a specific college."""
    try:
        college = db.query(College).filter(College.id == college_id).first()
        if not college:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "College not found",
                    "code": "COLLEGE_NOT_FOUND"
                }
            )
        schools = db.query(School).filter(School.college_id == college_id).all()
        return {
            "success": True,
            "message": "Schools retrieved successfully",
            "code": "SCHOOLS_RETRIEVED",
            "data": [{"id": s.id, "name": s.name, "college_id": s.college_id} for s in schools]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching schools: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred while fetching schools",
                "code": "SERVER_ERROR"
            }
        )

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring."""
    return {
        "success": True,
        "status": "healthy",
        "service": "authentication",
        "timestamp": datetime.utcnow().isoformat(),
        "code": "HEALTH_CHECK"
    }