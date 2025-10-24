from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from datetime import datetime
import logging
from typing import List, Optional
import json

from app.database import get_db
from app.models.registration import (
    Form, FormField, FormCondition, FormSubmission, 
    FormStatus, form_school_assignment
)
from app.models.student import School, College
from app.schemas.registration import (
    FormCreate, FormUpdate, FormResponse, FormField as FormFieldSchema,
    FormSubmissionResponse, FormAnalyticsResponse, FieldAnalytics
)
from app.auth.auth import get_current_admin
from app.services.gemini_service import generate_form_analytics

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/registrations", tags=["admin_registrations"])

# ========== FORM MANAGEMENT ==========
@router.post("/forms", response_model=FormResponse, status_code=status.HTTP_201_CREATED)
async def create_form(
    form_data: FormCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Create a new registration form (Admin only)"""
    logger.debug(f"Admin {current_admin.username} creating new form: {form_data.title}")
    
    try:
        # Validate schools exist
        if form_data.target_school_ids:
            schools = db.query(School).filter(School.id.in_(form_data.target_school_ids)).all()
            if len(schools) != len(form_data.target_school_ids):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="One or more schools not found"
                )
        
        # Create form with explicit status handling
        form_dict = form_data.dict(exclude_unset=True)
        # Ensure status is a valid FormStatus enum value
        if 'status' in form_dict:
            form_dict['status'] = FormStatus(form_dict['status']).value
        else:
            form_dict['status'] = FormStatus.DRAFT.value  # Default to lowercase 'draft'
        
        db_form = Form(
            title=form_dict['title'],
            description=form_dict.get('description'),
            created_by=current_admin.id,
            open_date=form_dict['open_date'],
            close_date=form_dict['close_date'],
            status=form_dict['status'],
            target_all_students=form_dict.get('target_all_students', False),
            target_years=form_dict.get('target_years', [])
        )
        db.add(db_form)
        db.flush()
        
        # Assign schools
        if form_data.target_school_ids:
            schools = db.query(School).filter(School.id.in_(form_data.target_school_ids)).all()
            db_form.assigned_schools = schools
        
        # Create fields
        for field_data in form_data.fields:
            db_field = FormField(
                form_id=db_form.id,
                label=field_data.label,
                field_type=field_data.field_type,
                required=field_data.required,
                options=field_data.options,
                default_value=field_data.default_value,
                position=field_data.position
            )
            db.add(db_field)
            db.flush()
            
            # Create conditions
            for condition_data in (field_data.conditions or []):
                db_condition = FormCondition(
                    field_id=db_field.id,
                    depends_on_field_id=condition_data.depends_on_field_id,
                    operator=condition_data.operator,
                    value=condition_data.value
                )
                db.add(db_condition)
        
        db.commit()
        db.refresh(db_form)
        
        logger.info(f"Admin {current_admin.username} created form ID {db_form.id}: {form_data.title}")
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
    status_filter: Optional[FormStatus] = None,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """List all forms (Admin only)"""
    logger.debug(f"Admin {current_admin.username} listing forms")
    
    query = db.query(Form)
    if status_filter:
        query = query.filter(Form.status == status_filter)
    
    forms = query.order_by(Form.created_at.desc()).offset(skip).limit(limit).all()
    return forms

@router.get("/forms/{form_id}", response_model=FormResponse)
async def get_form(
    form_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get a specific form (Admin only)"""
    logger.debug(f"Admin {current_admin.username} fetching form ID: {form_id}")
    
    db_form = db.query(Form).filter(Form.id == form_id).first()
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
    """Update a form (Admin only)"""
    logger.debug(f"Admin {current_admin.username} updating form ID: {form_id}")
    
    db_form = db.query(Form).filter(Form.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    try:
        update_data = form_data.dict(exclude_unset=True)
        
        # Ensure status is a valid FormStatus enum value
        if 'status' in update_data:
            update_data['status'] = FormStatus(update_data['status']).value
        
        # Handle target school updates
        if 'target_school_ids' in update_data:
            school_ids = update_data.pop('target_school_ids')
            schools = db.query(School).filter(School.id.in_(school_ids)).all()
            db_form.assigned_schools = schools
        
        # Update form fields
        for key, value in update_data.items():
            if value is not None:
                setattr(db_form, key, value)
        
        db_form.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(db_form)
        
        logger.info(f"Admin {current_admin.username} updated form ID {form_id}")
        return db_form
        
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
    """Delete a form (Admin only)"""
    logger.debug(f"Admin {current_admin.username} deleting form ID: {form_id}")
    
    db_form = db.query(Form).filter(Form.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    try:
        db.delete(db_form)
        db.commit()
        
        logger.info(f"Admin {current_admin.username} deleted form ID {form_id}")
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
    """Publish a form (change status to OPEN)"""
    logger.debug(f"Admin {current_admin.username} publishing form ID: {form_id}")
    
    db_form = db.query(Form).filter(Form.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    db_form.status = FormStatus.OPEN.value
    db.commit()
    db.refresh(db_form)
    
    logger.info(f"Form ID {form_id} published")
    return {"detail": "Form published", "status": db_form.status}

@router.post("/forms/{form_id}/close")
async def close_form(
    form_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Close a form (change status to CLOSED)"""
    logger.debug(f"Admin {current_admin.username} closing form ID: {form_id}")
    
    db_form = db.query(Form).filter(Form.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    db_form.status = FormStatus.CLOSED.value
    
    # Lock all submissions
    submissions = db.query(FormSubmission).filter(FormSubmission.form_id == form_id).all()
    for submission in submissions:
        submission.locked = True
    
    db.commit()
    db.refresh(db_form)
    
    logger.info(f"Form ID {form_id} closed and all submissions locked")
    return {"detail": "Form closed", "status": db_form.status}

# ========== FIELD MANAGEMENT ==========
@router.post("/forms/{form_id}/fields", response_model=FormFieldSchema)
async def add_field(
    form_id: int,
    field_data: FormFieldSchema,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Add a field to a form"""
    logger.debug(f"Adding field to form ID: {form_id}")
    
    db_form = db.query(Form).filter(Form.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    try:
        db_field = FormField(
            form_id=form_id,
            label=field_data.label,
            field_type=field_data.field_type,
            required=field_data.required,
            options=field_data.options,
            default_value=field_data.default_value,
            position=field_data.position
        )
        db.add(db_field)
        db.commit()
        db.refresh(db_field)
        
        logger.info(f"Field added to form ID {form_id}")
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
    logger.debug(f"Deleting field ID: {field_id} from form ID: {form_id}")
    
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
        
        logger.info(f"Field ID {field_id} deleted")
        return {"detail": "Field deleted"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting field: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting field: {str(e)}"
        )

# ========== SUBMISSIONS MANAGEMENT ==========
@router.get("/forms/{form_id}/submissions", response_model=List[FormSubmissionResponse])
async def list_form_submissions(
    form_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """List all submissions for a form"""
    logger.debug(f"Admin {current_admin.username} listing submissions for form ID: {form_id}")
    
    db_form = db.query(Form).filter(Form.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    submissions = db.query(FormSubmission).filter(
        FormSubmission.form_id == form_id
    ).offset(skip).limit(limit).all()
    
    return submissions

@router.get("/forms/{form_id}/submissions/{submission_id}", response_model=FormSubmissionResponse)
async def get_submission(
    form_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get a specific submission"""
    logger.debug(f"Fetching submission ID: {submission_id}")
    
    submission = db.query(FormSubmission).filter(
        and_(FormSubmission.id == submission_id, FormSubmission.form_id == form_id)
    ).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    return submission

@router.delete("/forms/{form_id}/submissions/{submission_id}")
async def delete_submission(
    form_id: int,
    submission_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Delete a submission"""
    logger.debug(f"Admin {current_admin.username} deleting submission ID: {submission_id}")
    
    submission = db.query(FormSubmission).filter(
        and_(FormSubmission.id == submission_id, FormSubmission.form_id == form_id)
    ).first()
    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )
    
    try:
        db.delete(submission)
        db.commit()
        
        logger.info(f"Submission ID {submission_id} deleted")
        return {"detail": "Submission deleted"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting submission: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting submission: {str(e)}"
        )

# ========== ANALYTICS & EXPORT ==========
@router.get("/forms/{form_id}/analytics", response_model=FormAnalyticsResponse)
async def get_form_analytics(
    form_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get analytics and AI-generated insights for a form"""
    logger.debug(f"Generating analytics for form ID: {form_id}")
    
    db_form = db.query(Form).filter(Form.id == form_id).first()
    if not db_form:
        raise HTTPException(status_code=404, detail="Form not found")
    
    submissions = db.query(FormSubmission).filter(
        FormSubmission.form_id == form_id
    ).all()
    
    total_submissions = len(submissions)
    
    # Calculate field analytics
    field_analytics = []
    for field in db_form.fields:
        responses = [sub.data.get(str(field.id)) for sub in submissions if str(field.id) in sub.data]
        
        response_breakdown = {}
        if field.field_type == "boolean":
            response_breakdown = {
                "true": sum(1 for r in responses if r is True),
                "false": sum(1 for r in responses if r is False)
            }
        elif field.field_type == "select":
            response_breakdown = {}
            for response in responses:
                response_breakdown[response] = response_breakdown.get(response, 0) + 1
        else:
            response_breakdown = {"total_responses": len(responses)}
        
        field_analytics.append(FieldAnalytics(
            field_id=field.id,
            field_label=field.label,
            field_type=field.field_type.value,
            total_responses=len(responses),
            response_breakdown=response_breakdown
        ))
    
    # Generate AI insights
    ai_summary = None
    ai_insights = None
    if total_submissions > 0:
        ai_summary, ai_insights = generate_form_analytics(
            form_title=db_form.title,
            fields=db_form.fields,
            submissions=submissions,
            field_analytics=field_analytics
        )
    
    return FormAnalyticsResponse(
        form_id=form_id,
        form_title=db_form.title,
        total_submissions=total_submissions,
        submission_percentage=100.0 if total_submissions > 0 else 0.0,
        submission_deadline=db_form.close_date,
        field_analytics=field_analytics,
        ai_summary=ai_summary,
        ai_insights=ai_insights
    )

@router.get("/forms/{form_id}/submissions/export")
async def export_submissions(
    form_id: int,
    format: str = Query("csv", regex="^(csv|json|xlsx)$"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Export form submissions in specified format"""
    logger.debug(f"Exporting submissions for form ID: {form_id} in {format} format")
    
    db_form = db.query(Form).filter(Form.id == form_id).first()
    if not db_form:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Form not found"
        )
    
    submissions = db.query(FormSubmission).filter(
        FormSubmission.form_id == form_id
    ).all()
    
    # Implementation depends on export service
    return {"message": f"Export in {format} format", "count": len(submissions)}