"""
COMPLETE ROUTES FILE - Full S3 Integration with File Upload Service
Replaces your entire app/routes/admin/registrations.py
Production-ready with all advanced features
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status, UploadFile, File, Request
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import logging
from typing import List, Optional, Dict, Any
import json
from enum import Enum
import hashlib
from pathlib import Path
import csv
import io
from fastapi.responses import StreamingResponse

from app.database import get_db
from app.models.registration import (
    Form as FormModel, FormField, FormCondition, FormSubmission, 
    FormStatus, FormFieldUpload, FormNotification, FormAuditLog,
    form_school_assignment, FieldType, SubmissionStatus, ConditionType
)
from app.models.student import School, College
from app.schemas.registration import (
    FormCreate, FormUpdate, FormResponse, FormFieldCreate, FormFieldResponse,
    FormSubmissionResponse, FormAnalyticsResponse, FieldAnalytics,
    FormSubmissionCreate, FormNotificationConfig, FormFieldUploadResponse
)
from app.auth.auth import get_current_admin, get_current_user
from app.services.s3_service import s3_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/registrations", tags=["admin_registrations"])
public_router = APIRouter(prefix="/forms", tags=["public_forms"])

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
    'pdf': 50 * 1024 * 1024,  # 50MB
    'doc': 25 * 1024 * 1024,  # 25MB
    'image': 10 * 1024 * 1024,  # 10MB
    'video': 500 * 1024 * 1024,  # 500MB
    'spreadsheet': 20 * 1024 * 1024,  # 20MB
    'archive': 100 * 1024 * 1024  # 100MB
}

# ========== FIELD TYPES & VALIDATORS ==========
class DynamicFieldType(str, Enum):
    """Extended field types for dynamic forms"""
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    EMAIL = "email"
    PHONE = "phone"
    NUMBER = "number"
    CURRENCY = "currency"
    DATE = "date"
    TIME = "time"
    DATETIME = "datetime"
    SELECT = "select"
    MULTI_SELECT = "multi_select"
    RADIO = "radio"
    CHECKBOX = "checkbox"
    BOOLEAN = "boolean"
    FILE_UPLOAD = "file_upload"
    MULTI_FILE_UPLOAD = "multi_file_upload"
    ADDRESS = "address"
    RATING = "rating"
    SIGNATURE = "signature"
    COUNTRY = "country"
    STATE = "state"
    LINKED_SELECT = "linked_select"


def validate_field_value(field: FormField, value: Any) -> bool:
    """Validate field value based on field type and constraints"""
    if value is None:
        return not field.required
    
    field_type = field.field_type.value
    
    if field_type == 'email':
        import re
        pattern = r'^[^\s@]+@[^\s@]+\.[^\s@]+$'
        return bool(re.match(pattern, str(value)))
    
    elif field_type == 'phone':
        # Remove common phone formatting
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


def validate_file_upload(
    file: UploadFile,
    allowed_types: List[str],
    max_size: int = 10 * 1024 * 1024
) -> bool:
    """Validate file before S3 upload"""
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
            detail=f"File type {content_type} not allowed. Allowed types: {', '.join(allowed_types)}"
        )
    
    return True


def get_file_type_category(content_type: str) -> str:
    """Determine file type category from content type"""
    for category, types in ALLOWED_FILE_TYPES.items():
        if content_type in types:
            return category
    return "unknown"


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
        
        # Validate file
        validate_file_upload(file, allowed_types, max_size)
        
        # Read file content
        file_content = await file.read()
        file_size = len(file_content)
        
        # Calculate file hash
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Determine file type
        file_type = get_file_type_category(file.content_type or "")
        
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
            content_type=file.content_type or "application/octet-stream"
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
            content_type=file.content_type or "application/octet-stream",
            s3_key=s3_key,
            s3_url=file_url,
            file_hash=file_hash,
            virus_scan_status="pending"  # Can integrate ClamAV here
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


# ========== FORM MANAGEMENT ROUTES ==========

@router.post("/forms", response_model=FormResponse, status_code=status.HTTP_201_CREATED)
async def create_form(
    form_data: FormCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Create a new registration form with advanced field types"""
    logger.debug(f"Admin {current_admin.id} creating form: {form_data.title}")
    
    try:
        # Validate schools
        if form_data.target_school_ids:
            schools = db.query(School).filter(School.id.in_(form_data.target_school_ids)).all()
            if len(schools) != len(form_data.target_school_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more schools not found"
                )
        
        status_value = form_data.status.value if form_data.status else FormStatus.draft.value
        
        # Create form
        db_form = FormModel(
            title=form_data.title,
            description=form_data.description,
            created_by=current_admin.id,
            open_date=form_data.open_date,
            close_date=form_data.close_date,
            status=status_value,
            target_all_students=form_data.target_all_students,
            target_years=form_data.target_years or [],
            allow_multiple_submissions=getattr(form_data, 'allow_multiple_submissions', False),
            require_authentication=getattr(form_data, 'require_authentication', True),
            enable_progress_bar=getattr(form_data, 'enable_progress_bar', True),
            enable_conditional_logic=getattr(form_data, 'enable_conditional_logic', True),
            collect_ip_address=getattr(form_data, 'collect_ip_address', False),
            randomize_field_order=getattr(form_data, 'randomize_field_order', False),
            form_type=getattr(form_data, 'form_type', 'registration'),
            tags=getattr(form_data, 'tags', []),
            metadata=getattr(form_data, 'metadata', {})
        )
        db.add(db_form)
        db.flush()
        
        # Assign schools
        if form_data.target_school_ids:
            schools = db.query(School).filter(School.id.in_(form_data.target_school_ids)).all()
            db_form.assigned_schools = schools
        
        # Create fields
        for position, field_data in enumerate(form_data.fields):
            try:
                # Validate field type
                field_type_enum = DynamicFieldType(field_data.field_type.value)
                
                db_field = FormField(
                    form_id=db_form.id,
                    label=field_data.label,
                    field_type=field_data.field_type.value,
                    required=field_data.required,
                    description=getattr(field_data, 'description', None),
                    options=field_data.options,
                    default_value=field_data.default_value,
                    position=position,
                    placeholder=getattr(field_data, 'placeholder', None),
                    help_text=getattr(field_data, 'help_text', None),
                    min_value=getattr(field_data, 'min_value', None),
                    max_value=getattr(field_data, 'max_value', None),
                    min_length=getattr(field_data, 'min_length', None),
                    max_length=getattr(field_data, 'max_length', None),
                    validation_rules=getattr(field_data, 'validation_rules', {}),
                    file_upload_config=getattr(field_data, 'file_upload_config', None),
                    width_percentage=getattr(field_data, 'width_percentage', 100),
                    is_section_header=getattr(field_data, 'is_section_header', False),
                    section_description=getattr(field_data, 'section_description', None),
                    depends_on_field_id=getattr(field_data, 'depends_on_field_id', None)
                )
                db.add(db_field)
                db.flush()
                
                # Create conditions
                for condition_data in (getattr(field_data, 'conditions', None) or []):
                    db_condition = FormCondition(
                        field_id=db_field.id,
                        depends_on_field_id=condition_data.depends_on_field_id,
                        operator=condition_data.operator,
                        value=condition_data.value,
                        condition_type=getattr(condition_data, 'condition_type', 'show')
                    )
                    db.add(db_condition)
                    
            except ValueError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid field type: {field_data.field_type}"
                )
        
        # Create audit log
        audit = FormAuditLog(
            form_id=db_form.id,
            admin_id=current_admin.id,
            action='create',
            entity_type='form',
            entity_id=db_form.id,
            changes=None
        )
        db.add(audit)
        
        db.commit()
        db.refresh(db_form)
        
        logger.info(f"Form {db_form.id} created by admin {current_admin.id}")
        return db_form
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error creating form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating form: {str(e)}"
        )


@router.get("/forms", response_model=List[FormResponse])
async def list_forms(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """List all forms with optional status filter"""
    logger.debug(f"Admin {current_admin.id} listing forms")
    
    query = db.query(FormModel)
    
    if status_filter:
        try:
            status_enum = FormStatus(status_filter)
            query = query.filter(FormModel.status == status_enum.value)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join([s.value for s in FormStatus])}"
            )
    
    forms = query.order_by(FormModel.created_at.desc()).offset(skip).limit(limit).all()
    return forms


@router.get("/forms/{form_id}", response_model=FormResponse)
async def get_form(
    form_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get a specific form with all fields"""
    logger.debug(f"Admin {current_admin.id} fetching form {form_id}")
    
    db_form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    return db_form


@router.put("/forms/{form_id}", response_model=FormResponse)
async def update_form(
    form_id: int,
    form_data: FormUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Update an existing form"""
    logger.debug(f"Admin {current_admin.id} updating form {form_id}")
    
    db_form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    try:
        update_data = form_data.dict(exclude_unset=True)
        changes = {}
        
        # Handle status
        if 'status' in update_data:
            old_status = db_form.status
            new_status = update_data['status'].value if update_data['status'] else db_form.status
            db_form.status = new_status
            changes['status'] = {'old': old_status, 'new': new_status}
        
        # Handle school updates
        if 'target_school_ids' in update_data:
            school_ids = update_data.pop('target_school_ids')
            if school_ids:
                schools = db.query(School).filter(School.id.in_(school_ids)).all()
                if len(schools) != len(school_ids):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="One or more schools not found"
                    )
                db_form.assigned_schools = schools
            else:
                db_form.assigned_schools = []
        
        # Update other fields
        for key, value in update_data.items():
            if value is not None and key != 'status':
                old_value = getattr(db_form, key, None)
                setattr(db_form, key, value)
                if old_value != value:
                    changes[key] = {'old': old_value, 'new': value}
        
        db_form.updated_at = datetime.utcnow()
        
        # Create audit log
        audit = FormAuditLog(
            form_id=form_id,
            admin_id=current_admin.id,
            action='update',
            entity_type='form',
            entity_id=form_id,
            changes=changes if changes else None
        )
        db.add(audit)
        
        db.commit()
        db.refresh(db_form)
        
        logger.info(f"Form {form_id} updated by admin {current_admin.id}")
        return db_form
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        logger.error(f"Error updating form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating form: {str(e)}"
        )


@router.delete("/forms/{form_id}")
async def delete_form(
    form_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Delete a form and all related data"""
    logger.debug(f"Admin {current_admin.id} deleting form {form_id}")
    
    db_form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    try:
        # Delete all file uploads from S3
        uploads = db.query(FormFieldUpload).join(FormSubmission).filter(
            FormSubmission.form_id == form_id
        ).all()
        
        for upload in uploads:
            try:
                s3_service.delete_file(upload.s3_url)
                logger.debug(f"Deleted S3 file: {upload.s3_key}")
            except Exception as e:
                logger.warning(f"Failed to delete S3 file {upload.s3_key}: {str(e)}")
        
        # Create audit log
        audit = FormAuditLog(
            form_id=form_id,
            admin_id=current_admin.id,
            action='delete',
            entity_type='form',
            entity_id=form_id,
            changes=None
        )
        db.add(audit)
        
        # Delete form (cascades to fields, conditions, submissions)
        db.delete(db_form)
        db.commit()
        
        logger.info(f"Form {form_id} deleted by admin {current_admin.id}")
        return {"detail": "Form deleted successfully"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting form: {str(e)}"
        )


@router.post("/forms/{form_id}/publish")
async def publish_form(
    form_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Publish a form (change status to open)"""
    logger.debug(f"Admin {current_admin.id} publishing form {form_id}")
    
    db_form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    if db_form.status == FormStatus.open.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Form is already open"
        )
    
    now = datetime.utcnow()
    if db_form.open_date > now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Form cannot be published before its open date"
        )
    
    if db_form.close_date < now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Form cannot be published after its close date"
        )
    
    old_status = db_form.status
    db_form.status = FormStatus.open.value
    
    # Create audit log
    audit = FormAuditLog(
        form_id=form_id,
        admin_id=current_admin.id,
        action='publish',
        entity_type='form',
        entity_id=form_id,
        changes={'status': {'old': old_status, 'new': FormStatus.open.value}}
    )
    db.add(audit)
    db.commit()
    db.refresh(db_form)
    
    logger.info(f"Form {form_id} published by admin {current_admin.id}")
    return {"detail": "Form published", "status": db_form.status}


@router.post("/forms/{form_id}/close")
async def close_form(
    form_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Close a form (change status to closed and lock submissions)"""
    logger.debug(f"Admin {current_admin.id} closing form {form_id}")
    
    db_form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    old_status = db_form.status
    db_form.status = FormStatus.closed.value
    
    # Lock all submissions
    submissions = db.query(FormSubmission).filter(FormSubmission.form_id == form_id).all()
    for submission in submissions:
        submission.locked = True
    
    # Create audit log
    audit = FormAuditLog(
        form_id=form_id,
        admin_id=current_admin.id,
        action='close',
        entity_type='form',
        entity_id=form_id,
        changes={'status': {'old': old_status, 'new': FormStatus.closed.value}}
    )
    db.add(audit)
    db.commit()
    db.refresh(db_form)
    
    logger.info(f"Form {form_id} closed by admin {current_admin.id}")
    return {"detail": "Form closed and locked", "status": db_form.status}


# ========== FIELD MANAGEMENT ROUTES ==========

@router.post("/forms/{form_id}/fields", response_model=FormFieldResponse)
async def add_field(
    form_id: int,
    field_data: FormFieldCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Add a new field to a form"""
    logger.debug(f"Adding field to form {form_id}")
    
    db_form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    try:
        db_field = FormField(
            form_id=form_id,
            label=field_data.label,
            field_type=field_data.field_type.value,
            required=field_data.required,
            description=getattr(field_data, 'description', None),
            options=field_data.options,
            default_value=field_data.default_value,
            position=field_data.position,
            placeholder=getattr(field_data, 'placeholder', None),
            help_text=getattr(field_data, 'help_text', None),
            min_value=getattr(field_data, 'min_value', None),
            max_value=getattr(field_data, 'max_value', None),
            min_length=getattr(field_data, 'min_length', None),
            max_length=getattr(field_data, 'max_length', None),
            validation_rules=getattr(field_data, 'validation_rules', {}),
            file_upload_config=getattr(field_data, 'file_upload_config', None),
            width_percentage=getattr(field_data, 'width_percentage', 100),
            is_section_header=getattr(field_data, 'is_section_header', False),
            section_description=getattr(field_data, 'section_description', None),
            depends_on_field_id=getattr(field_data, 'depends_on_field_id', None)
        )
        db.add(db_field)
        db.commit()
        db.refresh(db_field)
        
        logger.info(f"Field added to form {form_id}")
        return db_field
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error adding field: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error adding field: {str(e)}"
        )


@router.delete("/forms/{form_id}/fields/{field_id}")
async def delete_field(
    form_id: int,
    field_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Delete a field from a form"""
    logger.debug(f"Deleting field {field_id} from form {form_id}")
    
    db_field = db.query(FormField).filter(
        and_(FormField.id == field_id, FormField.form_id == form_id)
    ).first()
    
    if not db_field:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Field not found"
        )
    
    try:
        db.delete(db_field)
        db.commit()
        
        logger.info(f"Field {field_id} deleted")
        return {"detail": "Field deleted"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting field: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting field: {str(e)}"
        )


# ========== SUBMISSION MANAGEMENT ROUTES ==========

@router.get("/forms/{form_id}/submissions", response_model=List[FormSubmissionResponse])
async def list_submissions(
    form_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """List all submissions for a form"""
    logger.debug(f"Admin {current_admin.id} listing submissions for form {form_id}")
    
    db_form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    query = db.query(FormSubmission).filter(FormSubmission.form_id == form_id)
    
    if status_filter:
        try:
            status_enum = SubmissionStatus(status_filter)
            query = query.filter(FormSubmission.status == status_enum.value)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join([s.value for s in SubmissionStatus])}"
            )
    
    submissions = query.order_by(FormSubmission.submitted_at.desc()).offset(skip).limit(limit).all()
    return submissions


@router.get("/forms/{form_id}/submissions/{submission_id}", response_model=FormSubmissionResponse)
async def get_submission(
    form_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get a specific submission with all details"""
    logger.debug(f"Admin {current_admin.id} fetching submission {submission_id}")
    
    submission = db.query(FormSubmission).filter(
        and_(
            FormSubmission.id == submission_id,
            FormSubmission.form_id == form_id
        )
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    return submission


@router.get("/forms/{form_id}/submissions/{submission_id}/with-files")
async def get_submission_with_files(
    form_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get submission with file details and presigned download URLs"""
    logger.debug(f"Admin {current_admin.id} fetching submission {submission_id} with files")
    
    submission = db.query(FormSubmission).filter(
        and_(
            FormSubmission.id == submission_id,
            FormSubmission.form_id == form_id
        )
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
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
            logger.error(f"Error generating presigned URL for upload {upload.id}: {str(e)}")
            files.append({
                "id": upload.id,
                "filename": upload.original_filename,
                "error": "Failed to generate download URL"
            })
    
    return {
        "id": submission.id,
        "form_id": submission.form_id,
        "student_id": submission.student_id,
        "submitted_at": submission.submitted_at.isoformat(),
        "status": submission.status,
        "time_to_complete_seconds": submission.time_to_complete_seconds,
        "ip_address": submission.ip_address,
        "reviewed_by": submission.reviewed_by,
        "reviewed_at": submission.reviewed_at.isoformat() if submission.reviewed_at else None,
        "review_notes": submission.review_notes,
        "data": submission.data,
        "files": files
    }


@router.get("/forms/{form_id}/submissions/{submission_id}/files/{upload_id}")
async def download_submission_file(
    form_id: int,
    submission_id: int,
    upload_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Generate presigned URL for file download"""
    logger.debug(f"Admin {current_admin.id} requesting download for file {upload_id}")
    
    upload = db.query(FormFieldUpload).filter(
        and_(
            FormFieldUpload.id == upload_id,
            FormFieldUpload.submission_id == submission_id
        )
    ).first()
    
    if not upload:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        presigned_url = s3_service.generate_presigned_url(upload.s3_url, expiration=3600)
        return {
            "download_url": presigned_url,
            "filename": upload.original_filename,
            "file_size": upload.file_size,
            "expires_in_seconds": 3600
        }
    except Exception as e:
        logger.error(f"Error generating presigned URL: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate download link"
        )


@router.delete("/forms/{form_id}/submissions/{submission_id}")
async def delete_submission(
    form_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Delete a submission and associated files from S3"""
    logger.debug(f"Admin {current_admin.id} deleting submission {submission_id}")
    
    submission = db.query(FormSubmission).filter(
        and_(
            FormSubmission.id == submission_id,
            FormSubmission.form_id == form_id
        )
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    try:
        # Delete all files from S3
        for upload in submission.file_uploads:
            try:
                s3_service.delete_file(upload.s3_url)
                logger.debug(f"Deleted S3 file: {upload.s3_key}")
            except Exception as e:
                logger.warning(f"Failed to delete S3 file {upload.s3_key}: {str(e)}")
        
        # Create audit log
        audit = FormAuditLog(
            form_id=form_id,
            admin_id=current_admin.id,
            action='delete',
            entity_type='submission',
            entity_id=submission_id,
            changes=None
        )
        db.add(audit)
        
        # Delete submission
        db.delete(submission)
        db.commit()
        
        logger.info(f"Submission {submission_id} deleted by admin {current_admin.id}")
        return {"detail": "Submission deleted"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting submission: {str(e)}"
        )


@router.put("/forms/{form_id}/submissions/{submission_id}/review")
async def review_submission(
    form_id: int,
    submission_id: int,
    status: str = "reviewed",
    notes: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Review and approve/reject a submission"""
    logger.debug(f"Admin {current_admin.id} reviewing submission {submission_id}")
    
    submission = db.query(FormSubmission).filter(
        and_(
            FormSubmission.id == submission_id,
            FormSubmission.form_id == form_id
        )
    ).first()
    
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    # Validate status
    valid_statuses = ['reviewed', 'approved', 'rejected']
    if status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status. Must be: {valid_statuses}"
        )
    
    old_status = submission.status
    submission.status = status
    submission.reviewed_by = current_admin.id
    submission.reviewed_at = datetime.utcnow()
    submission.review_notes = notes
    
    # Create audit log
    audit = FormAuditLog(
        form_id=form_id,
        admin_id=current_admin.id,
        action='review',
        entity_type='submission',
        entity_id=submission_id,
        changes={'status': {'old': old_status, 'new': status}}
    )
    db.add(audit)
    db.commit()
    
    logger.info(f"Submission {submission_id} reviewed: {status} by admin {current_admin.id}")
    return {"detail": f"Submission {status}"}


# ========== PUBLIC FORM ROUTES ==========

@public_router.get("/{form_id}")
async def get_public_form(
    form_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Get form for public submission"""
    db_form = db.query(FormModel).filter(
        and_(
            FormModel.id == form_id,
            FormModel.status == FormStatus.open.value
        )
    ).first()
    
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found or not open for submissions"
        )
    
    # Check submission period
    now = datetime.utcnow()
    if not (db_form.open_date <= now <= db_form.close_date):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Form is not currently accepting submissions"
        )
    
    return db_form


@public_router.post("/{form_id}/submit")
async def submit_form_with_files(
    form_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Submit form with file uploads to S3"""
    logger.debug(f"User {current_user.id} submitting form {form_id}")
    
    db_form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    # Check form is open
    if db_form.status != FormStatus.open.value:
        raise HTTPException(status_code=403, detail="Form not open for submissions")
    
    # Check submission period
    now = datetime.utcnow()
    if not (db_form.open_date <= now <= db_form.close_date):
        raise HTTPException(status_code=403, detail="Form not within submission period")
    
    # Check multiple submissions
    existing = db.query(FormSubmission).filter(
        and_(
            FormSubmission.form_id == form_id,
            FormSubmission.student_id == current_user.id
        )
    ).first()
    
    if existing and not db_form.allow_multiple_submissions:
        raise HTTPException(status_code=403, detail="Already submitted this form")
    
    try:
        form_data = await request.form()
        submission_data = {}
        start_time = datetime.utcnow()
        
        # Create submission first (to get ID for file organization)
        db_submission = FormSubmission(
            form_id=form_id,
            student_id=current_user.id,
            status=SubmissionStatus.submitted.value,
            ip_address=request.client.host if request.client else None,
            user_agent=request.headers.get('user-agent'),
            submitted_at=datetime.utcnow(),
            data={}  # Will update after processing
        )
        db.add(db_submission)
        db.flush()
        
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
                            logger.error(f"Error uploading file: {str(e)}")
                            raise HTTPException(400, f"File upload failed: {str(e)}")
                
                # Store URLs in submission
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
        
        logger.info(f"Form {form_id} submitted by user {current_user.id} (submission {db_submission.id})")
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
        logger.error(f"Error submitting form: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error submitting form: {str(e)}"
        )


# ========== ANALYTICS ROUTES ==========

@router.get("/forms/{form_id}/analytics", response_model=FormAnalyticsResponse)
async def get_form_analytics(
    form_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get comprehensive analytics with file upload statistics"""
    logger.debug(f"Generating analytics for form {form_id}")
    
    db_form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not db_form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    submissions = db.query(FormSubmission).filter(
        FormSubmission.form_id == form_id
    ).all()
    
    total_submissions = len(submissions)
    
    # Calculate field analytics
    field_analytics = []
    for field in db_form.fields:
        responses = [
            sub.data.get(str(field.id)) 
            for sub in submissions 
            if str(field.id) in sub.data
        ]
        
        response_breakdown = {}
        
        if field.field_type == 'boolean':
            response_breakdown = {
                "true": sum(1 for r in responses if r is True),
                "false": sum(1 for r in responses if r is False)
            }
        elif field.field_type in ['select', 'radio']:
            for response in responses:
                response_breakdown[response] = response_breakdown.get(response, 0) + 1
        elif field.field_type in ['multi_select', 'checkbox']:
            for response in responses:
                if isinstance(response, list):
                    for item in response:
                        response_breakdown[item] = response_breakdown.get(item, 0) + 1
                else:
                    response_breakdown[response] = response_breakdown.get(response, 0) + 1
        elif field.field_type in ['file_upload', 'multi_file_upload']:
            file_count = sum(
                len(r) if isinstance(r, list) else (1 if r else 0) 
                for r in responses
            )
            response_breakdown = {
                "total_files_uploaded": file_count,
                "submissions_with_files": len([r for r in responses if r]),
                "avg_files_per_submission": file_count / len(responses) if responses else 0
            }
        else:
            response_breakdown = {"total_responses": len(responses)}
        
        field_analytics.append(FieldAnalytics(
            field_id=field.id,
            field_label=field.label,
            field_type=field.field_type,
            total_responses=len(responses),
            response_breakdown=response_breakdown
        ))
    
    return FormAnalyticsResponse(
        form_id=form_id,
        form_title=db_form.title,
        total_submissions=total_submissions,
        submission_percentage=100.0 if total_submissions > 0 else 0.0,
        submission_deadline=db_form.close_date,
        field_analytics=field_analytics
    )


# ========== EXPORT ROUTES ==========

@router.get("/forms/{form_id}/submissions/export")
async def export_submissions(
    form_id: int,
    format: str = Query("csv", regex="^(csv|json)$"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Export submissions in CSV or JSON format"""
    logger.debug(f"Exporting form {form_id} submissions as {format}")
    
    db_form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not db_form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    submissions = db.query(FormSubmission).filter(
        FormSubmission.form_id == form_id
    ).all()
    
    if format == "json":
        return {
            "form_id": form_id,
            "form_title": db_form.title,
            "total_submissions": len(submissions),
            "exported_at": datetime.utcnow().isoformat(),
            "submissions": [
                {
                    "id": sub.id,
                    "student_id": sub.student_id,
                    "submitted_at": sub.submitted_at.isoformat(),
                    "status": sub.status,
                    "data": sub.data,
                    "time_to_complete_seconds": sub.time_to_complete_seconds
                }
                for sub in submissions
            ]
        }
    
    else:  # CSV
        output = io.StringIO()
        
        # Get all unique field IDs
        all_field_ids = set()
        for sub in submissions:
            all_field_ids.update(sub.data.keys())
        
        # Create headers
        headers = [
            'Submission ID',
            'Student ID',
            'Submitted At',
            'Status',
            'Time to Complete (seconds)'
        ] + [f'Field_{fid}' for fid in sorted(all_field_ids)]
        
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        
        # Write rows
        for sub in submissions:
            row = {
                'Submission ID': sub.id,
                'Student ID': sub.student_id,
                'Submitted At': sub.submitted_at.isoformat(),
                'Status': sub.status,
                'Time to Complete (seconds)': sub.time_to_complete_seconds or ''
            }
            for field_id in all_field_ids:
                value = sub.data.get(field_id, '')
                if isinstance(value, list):
                    value = '; '.join(str(v) for v in value)
                row[f'Field_{field_id}'] = value
            writer.writerow(row)
        
        output.seek(0)
        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename=form_{form_id}_submissions.csv"}
        )


# ========== AUDIT LOG ROUTES ==========

@router.get("/forms/{form_id}/audit-logs")
async def get_form_audit_logs(
    form_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get audit trail for compliance tracking"""
    logger.debug(f"Getting audit logs for form {form_id}")
    
    db_form = db.query(FormModel).filter(FormModel.id == form_id).first()
    if not db_form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    logs = db.query(FormAuditLog).filter(
        FormAuditLog.form_id == form_id
    ).order_by(FormAuditLog.timestamp.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": log.id,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "admin_id": log.admin_id,
            "changes": log.changes,
            "timestamp": log.timestamp.isoformat()
        }
        for log in logs
    ]


# ========== FILE STATISTICS ROUTES ==========

@router.get("/forms/{form_id}/file-statistics")
async def get_file_statistics(
    form_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get file upload statistics for a form"""
    logger.debug(f"Getting file statistics for form {form_id}")
    
    uploads = db.query(FormFieldUpload).join(FormSubmission).filter(
        FormSubmission.form_id == form_id
    ).all()
    
    if not uploads:
        return {
            "form_id": form_id,
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0,
            "by_type": {},
            "clean_files": 0,
            "infected_files": 0,
            "pending_scan": 0
        }
    
    total_size = sum(u.file_size for u in uploads)
    
    type_breakdown = {}
    for upload in uploads:
        file_type = upload.file_type
        type_breakdown[file_type] = type_breakdown.get(file_type, 0) + 1
    
    return {
        "form_id": form_id,
        "total_files": len(uploads),
        "total_size_bytes": total_size,
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "by_type": type_breakdown,
        "clean_files": sum(1 for u in uploads if u.virus_scan_status == "clean"),
        "infected_files": sum(1 for u in uploads if u.virus_scan_status == "infected"),
        "pending_scan": sum(1 for u in uploads if u.virus_scan_status == "pending")
    }