from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import logging
from typing import List, Optional

from app.database import get_db
from app.models.registration import (
    Form, FormField, FormSubmission, FormStatus  # No alias - use lowercase 'open'
)
from app.models.student import Student as StudentModel, School
from app.schemas.registration import (
    FormResponse, FormSubmissionCreate, FormSubmissionUpdate, 
    FormSubmissionResponse, FormFieldSchema
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
        
        # Log enum for debugging
        logger.debug(f"FormStatus.open.value = '{FormStatus.open.value}'")
        
        # Query for open forms within date range
        query = db.query(Form).filter(
            and_(
                Form.status == FormStatus.open.value,  # FIXED: lowercase 'open'
                Form.open_date <= current_time,
                Form.close_date >= current_time
            )
        )
        
        forms = query.all()
        logger.debug(f"Retrieved {len(forms)} open forms from database")
        
        # Filter by target audience
        eligible_forms = []
        
        for form in forms:
            logger.debug(f"Checking form ID {form.id} (status: '{form.status}')")
            is_eligible = False
            
            # If targeting all students
            if form.target_all_students:
                is_eligible = True
            else:
                # Check school assignment
                if form.assigned_schools:
                    student_school_id = current_student.school_id
                    if any(s.id == student_school_id for s in form.assigned_schools):
                        # Check year match
                        if not form.target_years or current_student.year_of_study in form.target_years:
                            is_eligible = True
                # Check year-only filtering
                elif form.target_years and current_student.year_of_study in form.target_years:
                    is_eligible = True
            
            if is_eligible:
                eligible_forms.append(form)
        
        # Sort by newest first and paginate
        eligible_forms.sort(key=lambda x: x.created_at, reverse=True)
        paginated_forms = eligible_forms[skip:skip + limit]
        
        logger.info(f"Found {len(paginated_forms)} eligible forms for {current_student.email}")
        return paginated_forms
        
    except Exception as e:
        logger.error(f"Error listing available forms: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving available forms: {str(e)}"
        )

@router.get("/forms/{form_id}", response_model=FormResponse)
async def get_form_details(
    form_id: int,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    logger.debug(f"Student {current_student.email} fetching form ID: {form_id}")
    
    try:
        db_form = db.query(Form).filter(Form.id == form_id).first()
        if not db_form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        current_time = datetime.utcnow()
        if db_form.status != FormStatus.open.value or db_form.open_date > current_time:
            raise HTTPException(status_code=403, detail="Form is not currently open")
        
        # Eligibility check (same as list_available_forms)
        is_eligible = False
        if db_form.target_all_students:
            is_eligible = True
        else:
            if db_form.assigned_schools:
                if any(s.id == current_student.school_id for s in db_form.assigned_schools):
                    if not db_form.target_years or current_student.year_of_study in db_form.target_years:
                        is_eligible = True
            elif db_form.target_years and current_student.year_of_study in db_form.target_years:
                is_eligible = True
        
        if not is_eligible:
            raise HTTPException(status_code=403, detail="You are not eligible for this form")
        
        return db_form
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching form {form_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error retrieving form details")

# ========== FORM SUBMISSION ==========
@router.post("/forms/{form_id}/submit", response_model=FormSubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_form(
    form_id: int,
    submission_data: FormSubmissionCreate,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    logger.debug(f"Student {current_student.email} submitting form ID: {form_id}")
    
    try:
        db_form = db.query(Form).filter(Form.id == form_id).first()
        if not db_form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        current_time = datetime.utcnow()
        if db_form.status != FormStatus.open.value:
            raise HTTPException(status_code=400, detail="Form is no longer open")
        
        if current_time > db_form.close_date:
            raise HTTPException(status_code=400, detail="Submission deadline has passed")
        
        # Check for existing submission
        existing = db.query(FormSubmission).filter(
            FormSubmission.form_id == form_id,
            FormSubmission.student_id == current_student.id
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Already submitted. Use update endpoint.")
        
        # Validate required fields
        for field in db_form.fields:
            if field.required:
                field_id = str(field.id)
                if field_id not in submission_data.data:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field.label}")
        
        # Create submission
        db_submission = FormSubmission(
            form_id=form_id,
            student_id=current_student.id,
            data=submission_data.data,
            submitted_at=current_time,
            locked=False
        )
        db.add(db_submission)
        db.commit()
        db.refresh(db_submission)
        
        logger.info(f"Form {form_id} submitted by {current_student.email}")
        return db_submission
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Submit error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error submitting form")

@router.get("/forms/{form_id}/submission", response_model=FormSubmissionResponse)
async def get_student_submission(
    form_id: int,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    submission = db.query(FormSubmission).filter(
        FormSubmission.form_id == form_id,
        FormSubmission.student_id == current_student.id
    ).first()
    
    if not submission:
        raise HTTPException(status_code=404, detail="No submission found")
    
    return submission

@router.put("/forms/{form_id}/submission", response_model=FormSubmissionResponse)
async def update_student_submission(
    form_id: int,
    submission_data: FormSubmissionUpdate,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    logger.debug(f"Student {current_student.email} updating form ID: {form_id}")
    
    try:
        db_form = db.query(Form).filter(Form.id == form_id).first()
        if not db_form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        submission = db.query(FormSubmission).filter(
            FormSubmission.form_id == form_id,
            FormSubmission.student_id == current_student.id
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="No submission found")
        
        current_time = datetime.utcnow()
        if current_time > db_form.close_date:
            submission.locked = True
            db.commit()
            raise HTTPException(status_code=403, detail="Deadline passed - submission locked")
        
        if submission.locked:
            raise HTTPException(status_code=403, detail="Submission is locked")
        
        # Validate required fields
        for field in db_form.fields:
            if field.required:
                field_id = str(field.id)
                if field_id not in submission_data.data:
                    raise HTTPException(status_code=400, detail=f"Missing required field: {field.label}")
        
        # Update
        submission.data = submission_data.data
        submission.last_edited_at = current_time
        db.commit()
        db.refresh(submission)
        
        logger.info(f"Form {form_id} updated by {current_student.email}")
        return submission
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Update error: {str(e)}")
        raise HTTPException(status_code=500, detail="Error updating submission")

# ========== SUBMISSION HISTORY ==========
@router.get("/submissions", response_model=List[FormSubmissionResponse])
async def get_student_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    include_locked: bool = Query(True),
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    query = db.query(FormSubmission).filter(FormSubmission.student_id == current_student.id)
    
    if not include_locked:
        query = query.filter(FormSubmission.locked == False)
    
    submissions = query.order_by(FormSubmission.submitted_at.desc()).offset(skip).limit(limit).all()
    return submissions

# ========== FORM STATUS ==========
@router.get("/forms/{form_id}/status")
async def get_form_status(
    form_id: int,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    db_form = db.query(Form).filter(Form.id == form_id).first()
    if not db_form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    submission = db.query(FormSubmission).filter(
        FormSubmission.form_id == form_id,
        FormSubmission.student_id == current_student.id
    ).first()
    
    current_time = datetime.utcnow()
    time_remaining = max(0, (db_form.close_date - current_time).total_seconds())
    
    return {
        "form_id": form_id,
        "form_status": db_form.status,
        "submission_status": "submitted" if submission else "not_submitted",
        "is_locked": submission.locked if submission else False,
        "time_remaining_seconds": time_remaining,
        "deadline": db_form.close_date.isoformat(),
        "submitted_at": submission.submitted_at.isoformat() if submission else None,
        "last_edited_at": submission.last_edited_at.isoformat() if submission else None
    }