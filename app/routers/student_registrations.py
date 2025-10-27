# app/routers/registrations.py
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import logging
from typing import List

from app.database import get_db
from app.models.registration import Form, FormField, FormSubmission, FormStatus
from app.models.student import student as StudentModel, School
from app.schemas.registration import (
    FormResponse, FormSubmissionCreate, FormSubmissionUpdate, 
    FormSubmissionResponse, FormField as FormFieldSchema
)
from app.routers.students_sso import get_current_student

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/registrations", tags=["student_registrations"])

# ========== FORM DISCOVERY & RETRIEVAL ==========
@router.get("/forms", response_model=List[FormResponse])
async def list_available_forms(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    List all registration forms available to the student
    Forms are filtered based on:
    - Form status (must be open)
    - Target audience (school/college/year of study)
    - Current date (between open_date and close_date)
    """
    logger.debug(f"Student {current_student.email} listing available forms")
    
    try:
        current_time = datetime.utcnow()
        
        # Query for open forms within date range
        query = db.query(Form).filter(
            and_(
                Form.status == FormStatus.open.value,
                Form.open_date <= current_time,
                Form.close_date >= current_time
            )
        )
        
        forms = query.all()
        logger.debug(f"Retrieved {len(forms)} forms from database: {[f.id for f in forms]}")
        
        # Filter by target audience
        eligible_forms = []
        
        for form in forms:
            logger.debug(f"Checking eligibility for form ID {form.id}, status: {form.status}")
            is_eligible = False
            
            # If targeting all students
            if form.target_all_students:
                is_eligible = True
            else:
                # Check if student's school is in assigned schools
                if form.assigned_schools:
                    if current_student.school_id in [s.id for s in form.assigned_schools]:
                        # Check if year of study matches
                        if not form.target_years or current_student.year_of_study in form.target_years:
                            is_eligible = True
                # Check if only year filtering is applied
                elif form.target_years and current_student.year_of_study in form.target_years:
                    is_eligible = True
            
            if is_eligible:
                eligible_forms.append(form)
        
        # Sort by created date (newest first) and paginate
        eligible_forms = sorted(eligible_forms, key=lambda x: x.created_at, reverse=True)
        paginated_forms = eligible_forms[skip:skip + limit]
        
        logger.info(f"Found {len(paginated_forms)} available forms for student {current_student.email}")
        return paginated_forms
        
    except Exception as e:
        logger.error(f"Error listing available forms: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving available forms: {str(e)}"
        )

# ========== FORM SUBMISSION ==========
@router.post("/forms/{form_id}/submit", response_model=FormSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_form(
    form_id: int,
    submission_data: FormSubmissionCreate,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Submit a form response
    Students can only submit once per form
    If they already have a submission, use the update endpoint instead
    """
    logger.debug(f"Student {current_student.email} submitting form ID: {form_id}")
    
    try:
        db_form = db.query(Form).filter(Form.id == form_id).first()
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Check if form is open and within deadline
        current_time = datetime.utcnow()
        if db_form.status != FormStatus.open.value:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This form is no longer open for submissions"
            )
        
        if current_time > db_form.close_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="The submission deadline has passed"
            )
        
        # Check if student already has a submission
        existing_submission = db.query(FormSubmission).filter(
            and_(
                FormSubmission.form_id == form_id,
                FormSubmission.student_id == current_student.id
            )
        ).first()
        
        if existing_submission:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted this form. Use the update endpoint to modify your response."
            )
        
        # Validate required fields
        for field in db_form.fields:
            field_id_str = str(field.id)
            if field.required and field_id_str not in submission_data.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Required field '{field.label}' is missing"
                )
        
        # Create submission
        db_submission = FormSubmission(
            form_id=form_id,
            student_id=current_student.id,
            data=submission_data.data,
            submitted_at=current_time,
            last_edited_at=current_time,
            locked=False
        )
        db.add(db_submission)
        db.commit()
        db.refresh(db_submission)
        
        logger.info(f"Student {current_student.email} submitted form ID {form_id}")
        return db_submission
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting form: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error submitting form"
        )

@router.get("/forms/{form_id}/submission", response_model=FormSubmissionResponse)
async def get_student_submission(
    form_id: int,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Get the current student's submission for a form
    Returns 404 if no submission exists
    """
    logger.debug(f"Student {current_student.email} fetching their submission for form ID: {form_id}")
    
    try:
        submission = db.query(FormSubmission).filter(
            and_(
                FormSubmission.form_id == form_id,
                FormSubmission.student_id == current_student.id
            )
        ).first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You have not submitted this form yet"
            )
        
        return submission
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching student submission: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving submission"
        )

@router.put("/forms/{form_id}/submission", response_model=FormSubmissionResponse)
async def update_student_submission(
    form_id: int,
    submission_data: FormSubmissionUpdate,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Update an existing form submission
    Students can only edit before the form closes
    Submissions are automatically locked after deadline
    """
    logger.debug(f"Student {current_student.email} updating their submission for form ID: {form_id}")
    
    try:
        db_form = db.query(Form).filter(Form.id == form_id).first()
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        submission = db.query(FormSubmission).filter(
            and_(
                FormSubmission.form_id == form_id,
                FormSubmission.student_id == current_student.id
            )
        ).first()
        
        if not submission:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="You have not submitted this form yet. Please submit first."
            )
        
        # Check if submission is locked
        if submission.locked:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This form submission is locked and cannot be edited"
            )
        
        # Check if form is still within editing deadline
        current_time = datetime.utcnow()
        if current_time > db_form.close_date:
            # Auto-lock the submission
            submission.locked = True
            db.commit()
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="The submission deadline has passed. Your response is now locked."
            )
        
        # Validate required fields
        for field in db_form.fields:
            field_id_str = str(field.id)
            if field.required and field_id_str not in submission_data.data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Required field '{field.label}' is missing"
                )
        
        # Update submission
        submission.data = submission_data.data
        submission.last_edited_at = current_time
        db.commit()
        db.refresh(submission)
        
        logger.info(f"Student {current_student.email} updated form ID {form_id}")
        return submission
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating submission: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error updating submission"
        )

# ========== SUBMISSION HISTORY ==========
@router.get("/submissions", response_model=List[FormSubmissionResponse])
async def get_student_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    include_locked: bool = Query(True),
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Get all form submissions by the current student
    Includes both open and locked (past deadline) submissions
    """
    logger.debug(f"Student {current_student.email} fetching their submission history")
    
    try:
        query = db.query(FormSubmission).filter(
            FormSubmission.student_id == current_student.id
        )
        
        if not include_locked:
            query = query.filter(FormSubmission.locked == False)
        
        submissions = query.order_by(
            FormSubmission.submitted_at.desc()
        ).offset(skip).limit(limit).all()
        
        logger.info(f"Retrieved {len(submissions)} submissions for student {current_student.email}")
        return submissions
        
    except Exception as e:
        logger.error(f"Error fetching student submissions: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving submission history"
        )

# ========== FORM STATUS & METADATA ==========
@router.get("/forms/{form_id}/status")
async def get_form_status(
    form_id: int,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Get the status of a form and student's participation
    Returns:
    - Form status (open/closed/draft)
    - Submission status (submitted/not_submitted)
    - Time until deadline
    - Whether submission is locked
    """
    logger.debug(f"Student {current_student.email} checking status of form ID: {form_id}")
    
    try:
        db_form = db.query(Form).filter(Form.id == form_id).first()
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        submission = db.query(FormSubmission).filter(
            and_(
                FormSubmission.form_id == form_id,
                FormSubmission.student_id == current_student.id
            )
        ).first()
        
        current_time = datetime.utcnow()
        time_remaining = (db_form.close_date - current_time).total_seconds()
        
        return {
            "form_id": form_id,
            "form_status": db_form.status,
            "submission_status": "submitted" if submission else "not_submitted",
            "is_locked": submission.locked if submission else False,
            "time_remaining_seconds": max(0, time_remaining),
            "deadline": db_form.close_date.isoformat(),
            "submitted_at": submission.submitted_at.isoformat() if submission else None,
            "last_edited_at": submission.last_edited_at.isoformat() if submission else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching form status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving form status"
        )

# ========== AUTO-LOCK SUBMISSIONS (Task/Scheduled) ==========
async def auto_lock_expired_submissions(db: Session):
    """
    Auto-lock all submissions for forms that have passed their deadline
    Should be called periodically (e.g., every hour or minute)
    """
    try:
        current_time = datetime.utcnow()
        
        # Find all forms that have closed
        closed_forms = db.query(Form).filter(
            and_(
                Form.close_date <= current_time,
                Form.status == FormStatus.open.value
            )
        ).all()
        
        for form in closed_forms:
            # Lock all unlocked submissions
            submissions = db.query(FormSubmission).filter(
                and_(
                    FormSubmission.form_id == form.id,
                    FormSubmission.locked == False
                )
            ).all()
            
            for submission in submissions:
                submission.locked = True
            
            # Close the form
            form.status = FormStatus.closed.value
        
        db.commit()
        logger.info(f"Auto-locked {len(closed_forms)} forms and their submissions")
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error auto-locking submissions: {str(e)}", exc_info=True)

# Add this endpoint to your registrations.py file
# Place it after the list_available_forms endpoint and before the submit_form endpoint

@router.get("/forms/{form_id}", response_model=FormResponse)
async def get_form_details(
    form_id: int,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Get detailed information about a specific form including all fields
    Students can only access forms that are available to them
    """
    logger.debug(f"Student {current_student.email} fetching form ID: {form_id}")
    
    try:
        db_form = db.query(Form).filter(Form.id == form_id).first()
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Check if student is eligible to view this form
        current_time = datetime.utcnow()
        is_eligible = False
        
        # If targeting all students
        if db_form.target_all_students:
            is_eligible = True
        else:
            # Check if student's school is in assigned schools
            if db_form.assigned_schools:
                if current_student.school_id in [s.id for s in db_form.assigned_schools]:
                    # Check if year of study matches
                    if not db_form.target_years or current_student.year_of_study in db_form.target_years:
                        is_eligible = True
            # Check if only year filtering is applied
            elif db_form.target_years and current_student.year_of_study in db_form.target_years:
                is_eligible = True
        
        if not is_eligible:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not eligible to access this form"
            )
        
        # Check if form is within the available date range
        if current_time < db_form.open_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This form is not yet open"
            )
        
        logger.info(f"Student {current_student.email} accessed form ID {form_id}")
        return db_form
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching form details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving form details"
        )