from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app.models.student import student, College, School
from app.schemas.student import studentResponse
from app.auth.auth import get_current_admin
from typing import List, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/students", tags=["admin_students"])

# ==================== HELPER FUNCTIONS ====================

def get_student_response(db_student: student) -> dict:
    """Convert student model to response dictionary"""
    return {
        "id": db_student.id,
        "first_name": db_student.first_name,
        "last_name": db_student.last_name,
        "email": db_student.email,
        "phone_number": db_student.phone_number,
        "registration_number": db_student.registration_number,
        "college_id": db_student.college_id,
        "college_name": db_student.college.name if db_student.college else None,
        "school_id": db_student.school_id,
        "school_name": db_student.school.name if db_student.school else None,
        "course": db_student.course,
        "year_of_study": db_student.year_of_study,
        "is_active": db_student.is_active,
        "email_verified_at": db_student.email_verified_at,
        "created_at": db_student.created_at,
        "last_login": db_student.last_login,
    }

# ==================== ROUTES ====================

@router.get("/", response_model=dict)
def get_all_students(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of records to return"),
    search: Optional[str] = Query(None, description="Search by name, email, or registration number"),
    college_id: Optional[int] = Query(None, description="Filter by college ID"),
    school_id: Optional[int] = Query(None, description="Filter by school ID"),
    year_of_study: Optional[int] = Query(None, ge=1, le=6, description="Filter by year of study"),
    is_active: Optional[bool] = Query(None, description="Filter by verification status"),
    sort_by: str = Query("created_at", description="Sort field: created_at, last_login, first_name, email"),
    sort_order: str = Query("desc", description="Sort order: asc or desc"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get all students with advanced filtering, search, and pagination (Admin only)
    """
    logger.debug(f"Admin {current_admin.username} fetching students: skip={skip}, limit={limit}")
    
    try:
        # Base query
        query = db.query(student)
        
        # Apply search filter
        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    student.first_name.ilike(search_term),
                    student.last_name.ilike(search_term),
                    student.email.ilike(search_term),
                    student.registration_number.ilike(search_term),
                    student.course.ilike(search_term)
                )
            )
            logger.debug(f"Applied search filter: {search}")
        
        # Apply college filter
        if college_id is not None:
            query = query.filter(student.college_id == college_id)
            logger.debug(f"Applied college filter: {college_id}")
        
        # Apply school filter
        if school_id is not None:
            query = query.filter(student.school_id == school_id)
            logger.debug(f"Applied school filter: {school_id}")
        
        # Apply year of study filter
        if year_of_study is not None:
            query = query.filter(student.year_of_study == year_of_study)
            logger.debug(f"Applied year filter: {year_of_study}")
        
        # Apply verification status filter
        if is_active is not None:
            query = query.filter(student.is_active == is_active)
            logger.debug(f"Applied verification filter: {is_active}")
        
        # Get total count before pagination
        total_count = query.count()
        
        # Apply sorting
        sort_order_lower = sort_order.lower()
        if sort_order_lower not in ["asc", "desc"]:
            sort_order_lower = "desc"
        
        valid_sort_fields = ["created_at", "last_login", "first_name", "email", "year_of_study"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
        
        sort_column = getattr(student, sort_by)
        if sort_order_lower == "asc":
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())
        
        # Apply pagination
        students = query.offset(skip).limit(limit).all()
        
        # Convert to response format
        students_data = [get_student_response(student) for student in students]
        
        logger.info(f"Retrieved {len(students)} students (total: {total_count}) for admin {current_admin.username}")
        
        return {
            "success": True,
            "message": "Students retrieved successfully",
            "code": "STUDENTS_RETRIEVED",
            "data": students_data,
            "pagination": {
                "total": total_count,
                "skip": skip,
                "limit": limit,
                "returned": len(students)
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching students: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred while fetching students",
                "code": "SERVER_ERROR"
            }
        )


@router.get("/statistics", response_model=dict)
def get_student_statistics(
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get student statistics and analytics (Admin only)
    """
    logger.debug(f"Admin {current_admin.username} fetching student statistics")
    
    try:
        # Total students
        total_students = db.query(student).count()
        
        # Verified students
        verified_students = db.query(student).filter(student.is_active == True).count()
        
        # Unverified students
        unverified_students = db.query(student).filter(student.is_active == False).count()
        
        # Students by college
        students_by_college = db.query(
            College.name,
            func.count(student.id).label("count")
        ).join(College).group_by(College.name).all()
        
        # Students by year
        students_by_year = db.query(
            student.year_of_study,
            func.count(student.id).label("count")
        ).group_by(student.year_of_study).order_by(student.year_of_study).all()
        
        # Recent registrations (last 30 days)
        thirty_days_ago = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        from datetime import timedelta
        thirty_days_ago = thirty_days_ago - timedelta(days=30)
        recent_registrations = db.query(student).filter(
            student.created_at >= thirty_days_ago
        ).count()
        
        # Students with recent login (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        active_users = db.query(student).filter(
            student.last_login >= seven_days_ago
        ).count()
        
        logger.info(f"Student statistics retrieved by admin {current_admin.username}")
        
        return {
            "success": True,
            "message": "Student statistics retrieved successfully",
            "code": "STATISTICS_RETRIEVED",
            "data": {
                "total_students": total_students,
                "verified_students": verified_students,
                "unverified_students": unverified_students,
                "verification_rate": round((verified_students / total_students * 100) if total_students > 0 else 0, 2),
                "recent_registrations_30_days": recent_registrations,
                "active_users_7_days": active_users,
                "by_college": [
                    {"college": college, "count": count}
                    for college, count in students_by_college
                ],
                "by_year": [
                    {"year": year, "count": count}
                    for year, count in students_by_year
                ]
            }
        }
        
    except Exception as e:
        logger.error(f"Error fetching student statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred while fetching statistics",
                "code": "SERVER_ERROR"
            }
        )


@router.get("/{student_id}", response_model=dict)
def get_student_by_id(
    student_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Get a specific student by ID with full details (Admin only)
    """
    logger.debug(f"Admin {current_admin.username} fetching student ID: {student_id}")
    
    try:
        db_student = db.query(student).filter(student.id == student_id).first()
        
        if not db_student:
            logger.warning(f"Student ID {student_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Student not found",
                    "code": "STUDENT_NOT_FOUND"
                }
            )
        
        student_data = get_student_response(db_student)
        
        logger.info(f"Student ID {student_id} retrieved by admin {current_admin.username}")
        
        return {
            "success": True,
            "message": "Student retrieved successfully",
            "code": "STUDENT_RETRIEVED",
            "data": student_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student ID {student_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred while fetching student",
                "code": "SERVER_ERROR"
            }
        )


@router.put("/{student_id}", response_model=dict)
def update_student(
    student_id: int,
    first_name: Optional[str] = None,
    last_name: Optional[str] = None,
    email: Optional[str] = None,
    phone_number: Optional[str] = None,
    college_id: Optional[int] = None,
    school_id: Optional[int] = None,
    course: Optional[str] = None,
    year_of_study: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Update student information (Admin only)
    """
    logger.debug(f"Admin {current_admin.username} updating student ID: {student_id}")
    
    try:
        # Fetch the student
        db_student = db.query(student).filter(student.id == student_id).first()
        
        if not db_student:
            logger.warning(f"Student ID {student_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Student not found",
                    "code": "STUDENT_NOT_FOUND"
                }
            )
        
        updated = False
        changes_made = []
        
        # Update first name
        if first_name is not None:
            first_name_trimmed = first_name.strip()
            if first_name_trimmed and first_name_trimmed != db_student.first_name:
                if len(first_name_trimmed) < 1 or len(first_name_trimmed) > 50:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "success": False,
                            "message": "First name must be 1-50 characters",
                            "code": "INVALID_FIRST_NAME"
                        }
                    )
                db_student.first_name = first_name_trimmed
                updated = True
                changes_made.append("first_name")
        
        # Update last name
        if last_name is not None:
            last_name_trimmed = last_name.strip()
            if last_name_trimmed and last_name_trimmed != db_student.last_name:
                if len(last_name_trimmed) < 1 or len(last_name_trimmed) > 50:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "success": False,
                            "message": "Last name must be 1-50 characters",
                            "code": "INVALID_LAST_NAME"
                        }
                    )
                db_student.last_name = last_name_trimmed
                updated = True
                changes_made.append("last_name")
        
        # Update email
        if email is not None:
            email_trimmed = email.strip().lower()
            if email_trimmed != db_student.email:
                # Check if email already exists
                existing = db.query(student).filter(
                    student.email == email_trimmed,
                    student.id != student_id
                ).first()
                if existing:
                    raise HTTPException(
                        status_code=status.HTTP_409_CONFLICT,
                        detail={
                            "success": False,
                            "message": "This email is already in use by another student",
                            "code": "EMAIL_EXISTS"
                        }
                    )
                db_student.email = email_trimmed
                updated = True
                changes_made.append("email")
        
        # Update phone number
        if phone_number is not None:
            phone_trimmed = phone_number.strip() if phone_number else None
            if phone_trimmed != db_student.phone_number:
                db_student.phone_number = phone_trimmed
                updated = True
                changes_made.append("phone_number")
        
        # Update college and school
        if college_id is not None and college_id != db_student.college_id:
            college = db.query(College).filter(College.id == college_id).first()
            if not college:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Invalid college ID",
                        "code": "INVALID_COLLEGE"
                    }
                )
            db_student.college_id = college_id
            updated = True
            changes_made.append("college_id")
        
        if school_id is not None and school_id != db_student.school_id:
            # Verify school belongs to the college
            target_college_id = college_id if college_id is not None else db_student.college_id
            school = db.query(School).filter(
                School.id == school_id,
                School.college_id == target_college_id
            ).first()
            if not school:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Invalid school ID or school doesn't belong to the selected college",
                        "code": "INVALID_SCHOOL"
                    }
                )
            db_student.school_id = school_id
            updated = True
            changes_made.append("school_id")
        
        # Update course
        if course is not None:
            course_trimmed = course.strip()
            if course_trimmed and course_trimmed != db_student.course:
                db_student.course = course_trimmed
                updated = True
                changes_made.append("course")
        
        # Update year of study
        if year_of_study is not None and year_of_study != db_student.year_of_study:
            if year_of_study < 1 or year_of_study > 6:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "message": "Year of study must be between 1 and 6",
                        "code": "INVALID_YEAR"
                    }
                )
            db_student.year_of_study = year_of_study
            updated = True
            changes_made.append("year_of_study")
        
        # Update verification status
        if is_active is not None and is_active != db_student.is_active:
            db_student.is_active = is_active
            if is_active and not db_student.email_verified_at:
                db_student.email_verified_at = datetime.utcnow()
                # Clear verification token when manually activated
                db_student.verification_token = None
                db_student.verification_token_expiry = None
            updated = True
            changes_made.append("is_active")
        
        # If no changes detected, return existing student
        if not updated:
            logger.info(f"No changes detected for student ID {student_id} by admin {current_admin.username}")
            return {
                "success": True,
                "message": "No changes detected",
                "code": "NO_CHANGES",
                "data": get_student_response(db_student)
            }
        
        # Commit changes
        db.commit()
        db.refresh(db_student)
        
        logger.info(f"Admin {current_admin.username} updated student ID {student_id}. Changes: {', '.join(changes_made)}")
        
        return {
            "success": True,
            "message": f"Student updated successfully. Fields updated: {', '.join(changes_made)}",
            "code": "STUDENT_UPDATED",
            "data": get_student_response(db_student),
            "changes": changes_made
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating student ID {student_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred while updating student",
                "code": "SERVER_ERROR"
            }
        )


@router.delete("/{student_id}")
def delete_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Delete a student account (Admin only)
    Use with caution - this action cannot be undone
    """
    logger.debug(f"Admin {current_admin.username} attempting to delete student ID: {student_id}")
    
    try:
        db_student = db.query(student).filter(student.id == student_id).first()
        
        if not db_student:
            logger.warning(f"Student ID {student_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Student not found",
                    "code": "STUDENT_NOT_FOUND"
                }
            )
        
        student_email = db_student.email
        student_name = f"{db_student.first_name} {db_student.last_name}"
        
        # Delete the student
        db.delete(db_student)
        db.commit()
        
        logger.warning(f"Admin {current_admin.username} DELETED student: {student_email} (ID: {student_id}, Name: {student_name})")
        
        return {
            "success": True,
            "message": f"Student {student_name} ({student_email}) has been permanently deleted",
            "code": "STUDENT_DELETED"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting student ID {student_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred while deleting student",
                "code": "SERVER_ERROR"
            }
        )


@router.post("/{student_id}/verify")
def manually_verify_student(
    student_id: int,
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Manually verify a student's email (Admin only)
    """
    logger.debug(f"Admin {current_admin.username} manually verifying student ID: {student_id}")
    
    try:
        db_student = db.query(student).filter(student.id == student_id).first()
        
        if not db_student:
            logger.warning(f"Student ID {student_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "message": "Student not found",
                    "code": "STUDENT_NOT_FOUND"
                }
            )
        
        if db_student.is_active:
            return {
                "success": True,
                "message": "Student is already verified",
                "code": "ALREADY_VERIFIED",
                "data": get_student_response(db_student)
            }
        
        # Verify the student
        db_student.is_active = True
        db_student.email_verified_at = datetime.utcnow()
        db_student.verification_token = None
        db_student.verification_token_expiry = None
        
        db.commit()
        db.refresh(db_student)
        
        logger.info(f"Admin {current_admin.username} manually verified student: {db_student.email} (ID: {student_id})")
        
        return {
            "success": True,
            "message": f"Student {db_student.first_name} {db_student.last_name} has been manually verified",
            "code": "STUDENT_VERIFIED",
            "data": get_student_response(db_student)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying student ID {student_id}: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred while verifying student",
                "code": "SERVER_ERROR"
            }
        )


@router.post("/export")
def export_students(
    format: str = Query("json", description="Export format: json or csv"),
    college_id: Optional[int] = Query(None, description="Filter by college"),
    is_active: Optional[bool] = Query(None, description="Filter by verification status"),
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_admin)
):
    """
    Export student data in JSON or CSV format (Admin only)
    """
    logger.debug(f"Admin {current_admin.username} exporting students in {format} format")
    
    try:
        # Base query
        query = db.query(student)
        
        # Apply filters
        if college_id is not None:
            query = query.filter(student.college_id == college_id)
        
        if is_active is not None:
            query = query.filter(student.is_active == is_active)
        
        students = query.all()
        students_data = [get_student_response(db_student) for db_student in students]
        
        logger.info(f"Admin {current_admin.username} exported {len(students_data)} students")
        
        if format.lower() == "csv":
            # For CSV, you might want to use a library like pandas or csv
            # This is a simplified JSON response
            return {
                "success": True,
                "message": f"Exported {len(students_data)} students",
                "code": "STUDENTS_EXPORTED",
                "format": "csv",
                "note": "CSV export would require additional implementation with pandas or csv library",
                "data": students_data
            }
        
        return {
            "success": True,
            "message": f"Exported {len(students_data)} students",
            "code": "STUDENTS_EXPORTED",
            "format": "json",
            "count": len(students_data),
            "data": students_data
        }
        
    except Exception as e:
        logger.error(f"Error exporting students: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "message": "An error occurred while exporting students",
                "code": "SERVER_ERROR"
            }
        )