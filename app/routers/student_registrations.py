"""
COMPLETE STUDENT REGISTRATIONS ROUTES
Updated for enhanced dynamic form system with S3 file uploads
Production-ready with all advanced features
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime
import logging
from typing import List, Optional, Dict, Any
import hashlib
from pathlib import Path

from app.database import get_db
from app.models.registration import (
    Form, FormField, FormSubmission, FormStatus, FormFieldUpload,
    FormCondition, SubmissionStatus, ConditionType
)
from app.models.student import student as StudentModel, School
from app.schemas.registration import (
    FormResponse, FormSubmissionCreate, FormSubmissionUpdate, 
    FormSubmissionResponse, FormFieldCreate, FormFieldResponse,
    FormAnalyticsResponse, FieldAnalytics
)
from app.routers.students_sso import get_current_student
from app.services.s3_service import s3_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/registrations", tags=["student_registrations"])

# ========== FILE UPLOAD CONFIGURATION ==========
ALLOWED_FILE_TYPES = {
    'pdf': ['application/pdf'],
    'doc': ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
    'image': ['image/jpeg', 'image/png', 'image/webp', 'image/gif'],
    'video': ['video/mp4', 'video/quicktime', 'video/webm'],
    'spreadsheet': ['application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'],
    'archive': ['application/zip', 'application/x-rar-compressed', 'application/x-7z-compressed']
}

MAX_FILE_SIZES = {
    'pdf': 50 * 1024 * 1024,
    'doc': 25 * 1024 * 1024,
    'image': 10 * 1024 * 1024,
    'video': 500 * 1024 * 1024,
    'spreadsheet': 20 * 1024 * 1024,
    'archive': 100 * 1024 * 1024
}

# ========== HELPER FUNCTIONS ==========

def get_file_type_category(content_type: str) -> str:
    """Determine file type category from content type"""
    for category, types in ALLOWED_FILE_TYPES.items():
        if content_type in types:
            return category
    return "unknown"


def validate_field_value(field: FormField, value: Any) -> bool:
    """Validate field value based on field type and constraints"""
    if value is None:
        return not field.required
    
    field_type = field.field_type
    
    if field_type == 'email':
        import re
        pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        return bool(re.match(pattern, str(value)))
    
    elif field_type == 'phone':
        cleaned = ''.join(c for c in str(value) if c.isdigit())
        return 7 <= len(cleaned) <= 15
    
    elif field_type in ['number', 'currency']:
        try:
            num = float(value)
            if field.min_value is not None and num < field.min_value:
                return False
            if field.max_value is not None and num > field.max_value:
                return False
            return True
        except (ValueError, TypeError):
            return False
    
    elif field_type in ['select', 'radio']:
        if field.options is None:
            return True
        return value in field.options
    
    elif field_type in ['multi_select', 'checkbox']:
        if field.options is None:
            return True
        if not isinstance(value, list):
            return False
        return all(v in field.options for v in value)
    
    elif field_type == 'boolean':
        return isinstance(value, bool)
    
    elif field_type in ['date', 'time', 'datetime']:
        try:
            datetime.fromisoformat(str(value))
            return True
        except (ValueError, TypeError):
            return False
    
    elif field_type in ['short_text', 'long_text']:
        if field.min_length and len(str(value)) < field.min_length:
            return False
        if field.max_length and len(str(value)) > field.max_length:
            return False
        return True
    
    return True


def is_student_eligible_for_form(form: Form, student: StudentModel) -> bool:
    """Check if student is eligible to access the form"""
    # If targeting all students
    if form.target_all_students:
        return True
    
    # Check if student's school is in assigned schools
    if form.assigned_schools:
        if student.school_id in [s.id for s in form.assigned_schools]:
            # Check if year of study matches
            if not form.target_years or student.year_of_study in form.target_years:
                return True
    
    # Check if only year filtering is applied
    if form.target_years and student.year_of_study in form.target_years:
        return True
    
    return False


async def upload_form_file(
    file: UploadFile,
    submission_id: int,
    field_id: int,
    field: FormField,
    db: Session
) -> FormFieldUpload:
    """Upload file to S3 and create tracking record"""
    try:
        # Get file upload config
        upload_config = field.file_upload_config or {}
        allowed_types = upload_config.get('allowed_types', ['pdf', 'doc', 'image'])
        max_size = upload_config.get('max_size', 10 * 1024 * 1024)
        
        # Check file size
        if file.size and file.size > max_size:
            raise HTTPException(
                status_code=status.HTTP_413_PAYLOAD_TOO_LARGE,
                detail=f"File size exceeds {max_size / 1024 / 1024:.0f}MB limit"
            )
        
        # Check file type
        content_type = file.content_type or ""
        valid_types = []
        for type_key in allowed_types:
            valid_types.extend(ALLOWED_FILE_TYPES.get(type_key, []))
        
        if content_type not in valid_types:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"File type not allowed. Allowed: {', '.join(allowed_types)}"
            )
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Determine file type
        file_type = get_file_type_category(content_type)
        
        # Generate S3 key
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_ext = Path(file.filename).suffix.lower()
        safe_filename = Path(file.filename).stem.replace(' ', '_')[:100]
        
        s3_key = f"forms/submissions/submission_{submission_id}/field_{field_id}/{timestamp}_{safe_filename}{file_ext}"
        
        logger.debug(f"Uploading file to S3: {s3_key}")
        
        # Upload to S3
        file.file.seek(0)
        file_url = s3_service.upload_file(
            file=file,
            key=s3_key,
            content_type=content_type or "application/octet-stream"
        )
        
        if not file_url:
            raise Exception("S3 upload returned empty URL")
        
        # Create database record
        db_upload = FormFieldUpload(
            submission_id=submission_id,
            field_id=field_id,
            original_filename=file.filename,
            file_size=file_size,
            file_type=file_type,
            content_type=content_type or "application/octet-stream",
            s3_key=s3_key,
            s3_url=file_url,
            file_hash=file_hash,
            virus_scan_status="pending"
        )
        db.add(db_upload)
        
        logger.info(f"File uploaded successfully: {s3_key}")
        return db_upload
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading file: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


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
    
    Returns forms with all fields and conditional logic
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
        logger.debug(f"Retrieved {len(forms)} forms from database")
        
        # Filter by target audience
        eligible_forms = []
        
        for form in forms:
            if is_student_eligible_for_form(form, current_student):
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


@router.get("/forms/{form_id}", response_model=FormResponse)
async def get_form_details(
    form_id: int,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Get detailed information about a specific form including all fields
    
    Students can only access forms that are:
    - Targeted to them
    - Currently open
    - Within submission deadline
    
    Returns full form structure with fields, conditions, and file upload configs
    """
    logger.debug(f"Student {current_student.email} fetching form {form_id}")
    
    try:
        db_form = db.query(Form).filter(Form.id == form_id).first()
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Check eligibility
        if not is_student_eligible_for_form(db_form, current_student):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You are not eligible to access this form"
            )
        
        # Check if form is open
        if db_form.status != FormStatus.open.value:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This form is not open for submissions"
            )
        
        # Check date range
        current_time = datetime.utcnow()
        if current_time < db_form.open_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This form is not yet open"
            )
        
        if current_time > db_form.close_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This form is no longer accepting submissions"
            )
        
        logger.info(f"Student {current_student.email} accessed form {form_id}")
        return db_form
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching form details: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving form details"
        )


# ========== FORM SUBMISSION WITH FILE UPLOADS ==========

@router.post("/forms/{form_id}/submit", response_model=Dict[str, Any], status_code=status.HTTP_201_CREATED)
async def submit_form(
    form_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Submit a form with optional file uploads
    
    Supports:
    - Text fields (short_text, long_text, email, phone, etc.)
    - File uploads (single and multiple)
    - Selection fields (select, radio, checkbox, multi_select)
    - Date/Time fields
    - Number/Currency fields
    
    Content-Type: multipart/form-data
    {field_id}: value or file
    """
    logger.debug(f"Student {current_student.email} submitting form {form_id}")
    
    try:
        db_form = db.query(Form).filter(Form.id == form_id).first()
        if not db_form:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Form not found"
            )
        
        # Check eligibility
        if not is_student_eligible_for_form(db_form, current_student):
            raise HTTPException(status_code=403, detail="Not eligible for this form")
        
        # Check form is open
        if db_form.status != FormStatus.open.value:
            raise HTTPException(status_code=400, detail="Form not open for submissions")
        
        # Check deadline
        current_time = datetime.utcnow()
        if current_time > db_form.close_date:
            raise HTTPException(status_code=400, detail="Submission deadline has passed")
        
        # Check for existing submission (unless multiple allowed)
        existing = db.query(FormSubmission).filter(
            and_(
                FormSubmission.form_id == form_id,
                FormSubmission.student_id == current_student.id
            )
        ).first()
        
        if existing and not db_form.allow_multiple_submissions:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="You have already submitted this form"
            )
        
        # Create submission
        start_time = datetime.utcnow()
        db_submission = FormSubmission(
            form_id=form_id,
            student_id=current_student.id,
            status=SubmissionStatus.submitted.value,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            submitted_at=current_time,
            data={},
            locked=False
        )
        db.add(db_submission)
        db.flush()
        
        # Parse form data
        form_data = await request.form()
        submission_data = {}
        
        # Process each field
        for field in db_form.fields:
            field_id_str = str(field.id)
            
            # Handle file uploads
            if field.field_type in ['file_upload', 'multi_file_upload']:
                files = form_data.getlist(field_id_str)
                file_urls = []
                
                for file in files:
                    if file and isinstance(file, UploadFile):
                        try:
                            db_upload = await upload_form_file(
                                file, db_submission.id, field.id, field, db
                            )
                            file_urls.append(db_upload.s3_url)
                        except HTTPException:
                            raise
                        except Exception as e:
                            logger.error(f"File upload error: {str(e)}")
                            raise HTTPException(400, f"File upload failed: {str(e)}")
                
                # Store URLs
                if field.field_type == 'multi_file_upload':
                    submission_data[field_id_str] = file_urls
                else:
                    submission_data[field_id_str] = file_urls[0] if file_urls else None
            
            # Handle other field types
            else:
                value = form_data.get(field_id_str)
                if value:
                    # Validate field
                    if not validate_field_value(field, value):
                        raise HTTPException(
                            400, 
                            f"Invalid value for field '{field.label}'"
                        )
                    submission_data[field_id_str] = value
                elif field.required:
                    raise HTTPException(
                        400, 
                        f"Required field missing: {field.label}"
                    )
        
        # Calculate time to complete
        end_time = datetime.utcnow()
        time_seconds = int((end_time - start_time).total_seconds())
        
        # Update submission with data
        db_submission.data = submission_data
        db_submission.time_to_complete_seconds = time_seconds
        
        db.commit()
        db.refresh(db_submission)
        
        logger.info(f"Form {form_id} submitted by student {current_student.email}")
        return {
            "detail": "Form submitted successfully",
            "submission_id": db_submission.id,
            "time_to_complete_seconds": time_seconds
        }
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error submitting form: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting form: {str(e)}"
        )


@router.get("/forms/{form_id}/submission", response_model=FormSubmissionResponse)
async def get_student_submission(
    form_id: int,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Get the current student's submission for a form
    
    Returns:
    - All submitted data
    - File upload information with presigned URLs
    - Submission status and timestamps
    - Review status if approved/rejected
    """
    logger.debug(f"Student {current_student.email} fetching their submission for form {form_id}")
    
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
        logger.error(f"Error fetching submission: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving submission"
        )


@router.get("/forms/{form_id}/submission/with-files")
async def get_student_submission_with_files(
    form_id: int,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Get student's submission with file details and presigned download URLs
    
    Returns:
    - All form data
    - File information (name, size, type)
    - Presigned S3 URLs for downloading files
    - Submission review status
    """
    logger.debug(f"Student {current_student.email} fetching submission with files for form {form_id}")
    
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
        
        # Get file uploads with presigned URLs
        files = []
        for upload in submission.file_uploads:
            try:
                presigned_url = s3_service.generate_presigned_url(upload.s3_url, expiration=3600)
                files.append({
                    "id": upload.id,
                    "field_id": upload.field_id,
                    "filename": upload.original_filename,
                    "file_size": upload.file_size,
                    "file_type": upload.file_type,
                    "upload_timestamp": upload.upload_timestamp.isoformat(),
                    "virus_scan_status": upload.virus_scan_status,
                    "download_url": presigned_url
                })
            except Exception as e:
                logger.error(f"Error generating presigned URL: {str(e)}")
                files.append({
                    "id": upload.id,
                    "filename": upload.original_filename,
                    "error": "Failed to generate download URL"
                })
        
        return {
            "id": submission.id,
            "form_id": submission.form_id,
            "submitted_at": submission.submitted_at.isoformat(),
            "status": submission.status,
            "locked": submission.locked,
            "time_to_complete_seconds": submission.time_to_complete_seconds,
            "reviewed_by": submission.reviewed_by,
            "reviewed_at": submission.reviewed_at.isoformat() if submission.reviewed_at else None,
            "review_notes": submission.review_notes,
            "data": submission.data,
            "files": files
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching submission with files: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving submission"
        )


@router.get("/forms/{form_id}/submission/files/{upload_id}")
async def download_submission_file(
    form_id: int,
    upload_id: int,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Generate presigned URL for file download
    
    Only the student who submitted the form can download their files
    URLs expire after 1 hour
    """
    logger.debug(f"Student {current_student.email} requesting download for file {upload_id}")
    
    try:
        # Get student's submission
        submission = db.query(FormSubmission).filter(
            and_(
                FormSubmission.form_id == form_id,
                FormSubmission.student_id == current_student.id
            )
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="Submission not found")
        
        # Get file
        upload = db.query(FormFieldUpload).filter(
            and_(
                FormFieldUpload.id == upload_id,
                FormFieldUpload.submission_id == submission.id
            )
        ).first()
        
        if not upload:
            raise HTTPException(status_code=404, detail="File not found")
        
        # Generate presigned URL
        presigned_url = s3_service.generate_presigned_url(upload.s3_url, expiration=3600)
        
        return {
            "download_url": presigned_url,
            "filename": upload.original_filename,
            "file_size": upload.file_size,
            "expires_in_seconds": 3600
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating download link: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate download link")


@router.put("/forms/{form_id}/submission", response_model=FormSubmissionResponse)
async def update_student_submission(
    form_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Update an existing form submission
    
    Students can only edit before the form closes
    Submissions are automatically locked after deadline
    Can add/replace file uploads
    """
    logger.debug(f"Student {current_student.email} updating form {form_id}")
    
    try:
        db_form = db.query(Form).filter(Form.id == form_id).first()
        if not db_form:
            raise HTTPException(status_code=404, detail="Form not found")
        
        submission = db.query(FormSubmission).filter(
            and_(
                FormSubmission.form_id == form_id,
                FormSubmission.student_id == current_student.id
            )
        ).first()
        
        if not submission:
            raise HTTPException(status_code=404, detail="You have not submitted this form yet")
        
        # Check if locked
        if submission.locked:
            raise HTTPException(status_code=403, detail="This submission is locked and cannot be edited")
        
        # Check deadline
        current_time = datetime.utcnow()
        if current_time > db_form.close_date:
            submission.locked = True
            db.commit()
            raise HTTPException(status_code=403, detail="Submission deadline has passed")
        
        # Parse form data
        form_data = await request.form()
        submission_data = {}
        start_time = datetime.utcnow()
        
        # Process each field
        for field in db_form.fields:
            field_id_str = str(field.id)
            
            # Handle file uploads
            if field.field_type in ['file_upload', 'multi_file_upload']:
                files = form_data.getlist(field_id_str)
                file_urls = []
                
                if files:
                    # Delete old files if replacing
                    for old_upload in submission.file_uploads:
                        if old_upload.field_id == field.id:
                            try:
                                s3_service.delete_file(old_upload.s3_url)
                            except Exception as e:
                                logger.warning(f"Failed to delete old file: {str(e)}")
                            db.delete(old_upload)
                    
                    # Upload new files
                    for file in files:
                        if file and isinstance(file, UploadFile):
                            try:
                                db_upload = await upload_form_file(
                                    file, submission.id, field.id, field, db
                                )
                                file_urls.append(db_upload.s3_url)
                            except HTTPException:
                                raise
                
                # Store URLs
                if field.field_type == 'multi_file_upload':
                    submission_data[field_id_str] = file_urls
                else:
                    submission_data[field_id_str] = file_urls[0] if file_urls else submission.data.get(field_id_str)
            
            # Handle other field types
            else:
                value = form_data.get(field_id_str)
                if value:
                    if not validate_field_value(field, value):
                        raise HTTPException(400, f"Invalid value for field '{field.label}'")
                    submission_data[field_id_str] = value
                elif field.required:
                    raise HTTPException(400, f"Required field missing: {field.label}")
                else:
                    # Keep existing value if not provided
                    submission_data[field_id_str] = submission.data.get(field_id_str)
        
        # Calculate time to complete
        end_time = datetime.utcnow()
        time_seconds = int((end_time - start_time).total_seconds())
        
        # Update submission
        submission.data = submission_data
        submission.last_edited_at = current_time
        if submission.time_to_complete_seconds:
            submission.time_to_complete_seconds += time_seconds
        else:
            submission.time_to_complete_seconds = time_seconds
        
        db.commit()
        db.refresh(submission)
        
        logger.info(f"Form {form_id} updated by student {current_student.email}")
        return submission
        
    except HTTPException:
        db.rollback()
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating submission: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating submission: {str(e)}")


# ========== SUBMISSION HISTORY ==========

@router.get("/submissions", response_model=List[FormSubmissionResponse])
async def get_student_submissions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    include_locked: bool = Query(True),
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_student: StudentModel = Depends(get_current_student)
):
    """
    Get all form submissions by the current student
    
    Supports filtering by:
    - Status (submitted, reviewed, approved, rejected)
    - Locked/unlocked
    - Date range (via pagination)
    
    Returns submissions with all details
    """
    logger.debug(f"Student {current_student.email} fetching submission history")
    
    try:
        query = db.query(FormSubmission).filter(
            FormSubmission.student_id == current_student.id
        )
        
        if not include_locked:
            query = query.filter(FormSubmission.locked == False)
        
        if status_filter:
            query = query.filter(FormSubmission.status == status_filter)
        
        submissions = query.order_by(
            FormSubmission.submitted_at.desc()
        ).offset(skip).limit(limit).all()
        
        return submissions
    except Exception as e:
        logger.error(f"Error fetching student submissions: {str(e)}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error retrieving submission history")