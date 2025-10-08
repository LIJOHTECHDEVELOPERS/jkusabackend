## app/routers/admin/resources.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.resource import Resource
from app.schemas.resource import ResourceCreate, Resource as ResourceSchema
from app.auth.auth import get_current_admin
from app.services.s3_service import s3_service
from typing import List, Optional
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/resources", tags=["admin_resources"])
public_resource_router = APIRouter(prefix="/resources", tags=["public_resources"])

def generate_slug(title: str, db: Session, resource_id: int = None) -> str:
    """Generate a unique slug from the title."""
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    base_slug = slug
    counter = 1
    while True:
        query = db.query(Resource).filter(Resource.slug == slug)
        if resource_id:
            query = query.filter(Resource.id != resource_id)
        
        if not query.first():
            return slug
        
        slug = f"{base_slug}-{counter}"
        counter += 1

def upload_pdf(pdf: UploadFile) -> str:
    """Upload PDF to S3"""
    try:
        # Assuming s3_service has a method upload_pdf or similar; adjust if it's general upload_file
        pdf_url = s3_service.upload_pdf(pdf)
        return pdf_url
    except Exception as e:
        logger.error(f"Error uploading PDF: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to upload PDF: {str(e)}")

@public_resource_router.get("/", response_model=List[ResourceSchema])
def read_public_resources(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all resources with pagination (Public access)"""
    logger.debug(f"Accessing public resources: skip={skip}, limit={limit}")
    try:
        resources = db.query(Resource).order_by(Resource.id.desc()).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(resources)} resources")
        return resources
    except Exception as e:
        logger.error(f"Error fetching public resources: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@public_resource_router.get("/slug/{slug}", response_model=ResourceSchema)
def read_public_resource_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get a specific resource by slug (Public access)"""
    logger.debug(f"Fetching public resource by slug: {slug}")
    try:
        db_resource = db.query(Resource).filter(Resource.slug == slug).first()
        if db_resource is None:
            logger.warning(f"Resource with slug {slug} not found")
            raise HTTPException(status_code=404, detail="Resource not found")
        logger.info(f"Retrieved resource with slug: {slug}")
        return db_resource
    except Exception as e:
        logger.error(f"Error fetching resource by slug {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@public_resource_router.get("/{resource_id}", response_model=ResourceSchema)
def read_public_resource(
    resource_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific resource by ID (Public access)"""
    logger.debug(f"Fetching public resource ID: {resource_id}")
    try:
        db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
        if db_resource is None:
            logger.warning(f"Resource ID {resource_id} not found")
            raise HTTPException(status_code=404, detail="Resource not found")
        logger.info(f"Retrieved resource ID: {resource_id}")
        return db_resource
    except Exception as e:
        logger.error(f"Error fetching resource ID {resource_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=ResourceSchema)
async def create_resource(
    title: str = Form(..., min_length=1, max_length=200),
    description: str = Form(..., min_length=1),
    pdf: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Create a new resource with PDF upload (Admin only)"""
    logger.debug(f"Creating resource by admin: {current_admin.username} (ID: {current_admin.id})")
    
    pdf_url = None
    try:
        # Validate PDF
        if not pdf.content_type == 'application/pdf':
            logger.error(f"Invalid file type: {pdf.content_type}")
            raise HTTPException(status_code=400, detail="File must be a PDF")
        if pdf.size > 10 * 1024 * 1024:
            logger.error(f"PDF too large: {pdf.size} bytes")
            raise HTTPException(status_code=400, detail="PDF must be less than 10MB")
        
        # Upload PDF
        logger.debug(f"Uploading PDF: {pdf.filename}")
        pdf_url = upload_pdf(pdf)
        if not pdf_url:
            logger.error("Failed to upload PDF")
            raise HTTPException(status_code=500, detail="Failed to upload PDF")
        logger.debug(f"PDF uploaded successfully: {pdf_url}")

        # Generate unique slug
        slug = generate_slug(title, db)
        logger.debug(f"Generated slug: {slug}")

        # Create resource
        db_resource = Resource(
            title=title.strip(),
            description=description.strip(),
            pdf_url=pdf_url,
            slug=slug,
            # ➡️ FIX APPLIED HERE: Pass the authenticated admin's ID
            admin_id=current_admin.id 
        )
        db.add(db_resource)
        db.commit()
        db.refresh(db_resource)
        
        logger.info(f"Admin {current_admin.username} created resource ID {db_resource.id}: {title} (slug: {slug})")
        return db_resource
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        if pdf_url:
            try:
                s3_service.delete_file(pdf_url)  # Assuming delete_file or similar; adjust if delete_pdf
                logger.debug(f"Cleaned up uploaded PDF: {pdf_url}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup uploaded PDF: {cleanup_error}")
        
        logger.error(f"Error creating resource: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating resource: {str(e)}")

@router.get("/{resource_id}", response_model=ResourceSchema)
def read_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get a specific resource by ID (Admin only)"""
    logger.debug(f"Admin {current_admin.username} fetching resource ID: {resource_id}")
    db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if db_resource is None:
        logger.warning(f"Resource ID {resource_id} not found")
        raise HTTPException(status_code=404, detail="Resource not found")
    return db_resource

@router.get("/", response_model=List[ResourceSchema])
def read_resources(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get all resources with pagination (Admin only)"""
    logger.debug(f"Admin {current_admin.username} fetching resources: skip={skip}, limit={limit}")
    resources = db.query(Resource).order_by(Resource.id.desc()).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(resources)} resources for admin")
    return resources

@router.put("/{resource_id}", response_model=ResourceSchema)
async def update_resource(
    resource_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    pdf: Optional[UploadFile] = File(None),
    remove_pdf: Optional[str] = Form("false"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Update an existing resource with PDF handling (Admin only)"""
    logger.debug(f"Updating resource ID: {resource_id} by admin: {current_admin.username}")
    logger.debug(f"Received parameters:")
    logger.debug(f"  - title: {title}")
    logger.debug(f"  - description: {description[:50] + '...' if description and len(description) > 50 else description}")
    logger.debug(f"  - pdf: {pdf.filename if pdf else None}")
    logger.debug(f"  - remove_pdf: {remove_pdf}")
    
    # Fetch the existing resource
    db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if db_resource is None:
        logger.warning(f"Resource ID {resource_id} not found")
        raise HTTPException(status_code=404, detail="Resource not found")

    # Log current resource state
    logger.debug(f"Current resource state:")
    logger.debug(f"  - title: {db_resource.title}")
    logger.debug(f"  - slug: {db_resource.slug}")
    logger.debug(f"  - description: {db_resource.description[:50] + '...' if len(db_resource.description) > 50 else db_resource.description}")
    logger.debug(f"  - pdf_url: {db_resource.pdf_url}")

    new_pdf_url = None
    old_pdf_url = db_resource.pdf_url
    updated = False
    changes_made = []
    
    try:
        # Validate new PDF if provided
        if pdf:
            if not pdf.content_type == 'application/pdf':
                logger.error(f"Invalid file type: {pdf.content_type}")
                raise HTTPException(status_code=400, detail="File must be a PDF")
            if pdf.size > 10 * 1024 * 1024:
                logger.error(f"PDF too large: {pdf.size} bytes")
                raise HTTPException(status_code=400, detail="PDF must be less than 10MB")
        
        # Update title and regenerate slug if changed
        if title is not None:
            title_trimmed = title.strip()
            if title_trimmed != db_resource.title:
                if len(title_trimmed) < 1 or len(title_trimmed) > 200:
                    logger.error(f"Invalid title length: {len(title_trimmed)}")
                    raise HTTPException(status_code=400, detail="Title must be 1-200 characters")
                
                logger.debug(f"Title change detected: '{db_resource.title}' -> '{title_trimmed}'")
                db_resource.title = title_trimmed
                
                # Regenerate slug when title changes
                new_slug = generate_slug(title_trimmed, db, resource_id)
                logger.debug(f"Slug updated: '{db_resource.slug}' -> '{new_slug}'")
                db_resource.slug = new_slug
                
                updated = True
                changes_made.append("title")
                changes_made.append("slug")
            else:
                logger.debug("Title unchanged")

        # Update description
        if description is not None:
            description_trimmed = description.strip()
            if description_trimmed != db_resource.description:
                if len(description_trimmed) < 1:
                    logger.error("Description cannot be empty")
                    raise HTTPException(status_code=400, detail="Description must not be empty")
                
                logger.debug(f"Description change detected (length: {len(db_resource.description)} -> {len(description_trimmed)})")
                db_resource.description = description_trimmed
                updated = True
                changes_made.append("description")
            else:
                logger.debug("Description unchanged")

        # Handle PDF update or removal
        if pdf:
            # Upload new PDF
            logger.debug(f"Uploading new PDF: {pdf.filename}")
            new_pdf_url = upload_pdf(pdf)
            if not new_pdf_url:
                logger.error("Failed to upload PDF")
                raise HTTPException(status_code=500, detail="Failed to upload PDF")
            
            logger.debug(f"PDF change detected: '{db_resource.pdf_url}' -> '{new_pdf_url}'")
            db_resource.pdf_url = new_pdf_url
            updated = True
            changes_made.append("pdf")
            
        elif remove_pdf == "true" and db_resource.pdf_url:
            logger.debug(f"Removing existing PDF: {db_resource.pdf_url}")
            db_resource.pdf_url = None
            updated = True
            changes_made.append("removed_pdf")

        # Log update summary
        logger.debug(f"Update summary:")
        logger.debug(f"  - Changes detected: {updated}")
        logger.debug(f"  - Fields changed: {changes_made}")

        # Handle the case when no changes are detected
        if not updated:
            logger.info("No changes detected - returning existing resource without error")
            return db_resource

        # Commit changes
        db.commit()
        db.refresh(db_resource)
        
        # Delete old PDF if new one was uploaded successfully
        if new_pdf_url and old_pdf_url:
            try:
                s3_service.delete_file(old_pdf_url)  # Assuming delete_file or similar
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete old PDF: {cleanup_error}")
            
        # Delete old PDF if removal was requested
        if remove_pdf == "true" and old_pdf_url:
            try:
                s3_service.delete_file(old_pdf_url)
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete removed PDF: {cleanup_error}")
        
        logger.info(f"Admin {current_admin.username} updated resource ID {resource_id}. Changes: {', '.join(changes_made)}")
        return db_resource
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        if new_pdf_url:
            try:
                s3_service.delete_file(new_pdf_url)
                logger.debug(f"Cleaned up uploaded PDF after error: {new_pdf_url}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup uploaded PDF: {cleanup_error}")
        
        logger.error(f"Error updating resource: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating resource: {str(e)}")

@router.delete("/{resource_id}")
def delete_resource(
    resource_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Delete a resource (Admin only)"""
    logger.debug(f"Deleting resource ID: {resource_id} by admin: {current_admin.username}")
    db_resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if db_resource is None:
        logger.warning(f"Resource ID {resource_id} not found")
        raise HTTPException(status_code=404, detail="Resource not found")

    pdf_url = db_resource.pdf_url
    
    try:
        db.delete(db_resource)
        db.commit()
        
        if pdf_url:
            try:
                s3_service.delete_file(pdf_url)  # Assuming delete_file or similar
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete PDF from S3: {cleanup_error}")
        
        logger.info(f"Admin {current_admin.username} deleted resource ID {resource_id}")
        return {"detail": "Resource deleted"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting resource: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting resource: {str(e)}")