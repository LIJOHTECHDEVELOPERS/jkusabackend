from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.announcement import Announcement
from app.schemas.announcement import Announcement as AnnouncementSchema, AnnouncementCreate
from app.auth.auth import get_current_admin  # Changed to admin auth
from app.services.s3_service import s3_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Admin router for announcement management
admin_router = APIRouter(prefix="/admin/announcements", tags=["admin_announcements"])

# Public router for viewing announcements
public_router = APIRouter(prefix="/announcements", tags=["public_announcements"])

# ADMIN ENDPOINTS (existing code)
@admin_router.post("/", response_model=AnnouncementSchema)
async def create_announcement(
    title: str = Form(..., min_length=1, max_length=200),
    content: str = Form(..., min_length=1),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)  # Using admin auth
):
    """Create a new announcement (Admin only)"""
    image_url = None
    try:
        # Validate image if provided
        if image:
            if not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
        
        # Handle image upload if provided
        if image:
            image_url = s3_service.upload_image(image)
            if not image_url:
                raise HTTPException(status_code=500, detail="Failed to upload image")

        # Create announcement
        db_announcement = Announcement(
            title=title,
            content=content,
            image_url=image_url,
            announced_at=datetime.utcnow()
        )
        db.add(db_announcement)
        db.commit()
        db.refresh(db_announcement)
        
        logger.info(f"Admin {current_admin.username} created announcement: {title}")
        return db_announcement
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Clean up S3 image if upload succeeded but DB operation failed
        if image_url:
            try:
                s3_service.delete_image(image_url)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup uploaded image: {cleanup_error}")
        
        logger.error(f"Error creating announcement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating announcement: {str(e)}")

@admin_router.get("/{announcement_id}", response_model=AnnouncementSchema)
def read_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)  # Using admin auth
):
    """Get a specific announcement by ID (Admin only)"""
    db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if db_announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")
    return db_announcement

@admin_router.get("/", response_model=List[AnnouncementSchema])
def read_announcements(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)  # Using admin auth
):
    """Get all announcements with pagination (Admin only)"""
    announcements = db.query(Announcement).order_by(Announcement.announced_at.desc()).offset(skip).limit(limit).all()
    return announcements

@admin_router.put("/{announcement_id}", response_model=AnnouncementSchema)
async def update_announcement(
    announcement_id: int,
    title: str = Form(..., min_length=1, max_length=200),
    content: str = Form(..., min_length=1),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)  # Using admin auth
):
    """Update an existing announcement (Admin only)"""
    db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if db_announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")

    new_image_url = None
    old_image_url = db_announcement.image_url
    
    try:
        # Validate image if provided
        if image:
            if not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            if image.size > 5 * 1024 * 1024:  # 5MB limit
                raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
        
        # Handle image upload if provided
        if image:
            new_image_url = s3_service.upload_image(image)
            if not new_image_url:
                raise HTTPException(status_code=500, detail="Failed to upload image")

        # Update announcement
        db_announcement.title = title
        db_announcement.content = content
        if new_image_url:
            db_announcement.image_url = new_image_url
        
        db.commit()
        db.refresh(db_announcement)
        
        # Delete old image after successful update
        if new_image_url and old_image_url:
            try:
                s3_service.delete_image(old_image_url)
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete old image: {cleanup_error}")
        
        logger.info(f"Admin {current_admin.username} updated announcement {announcement_id}")
        return db_announcement
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        # Clean up new image if upload succeeded but DB operation failed
        if new_image_url:
            try:
                s3_service.delete_image(new_image_url)
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup uploaded image: {cleanup_error}")
        
        logger.error(f"Error updating announcement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating announcement: {str(e)}")

@admin_router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)  # Using admin auth
):
    """Delete an announcement (Admin only)"""
    db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
    if db_announcement is None:
        raise HTTPException(status_code=404, detail="Announcement not found")

    image_url = db_announcement.image_url
    
    try:
        db.delete(db_announcement)
        db.commit()
        
        # Delete image from S3 if exists
        if image_url:
            try:
                s3_service.delete_image(image_url)
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete image from S3: {cleanup_error}")
        
        logger.info(f"Admin {current_admin.username} deleted announcement {announcement_id}")
        return {"message": "Announcement deleted successfully", "deleted_id": announcement_id}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting announcement: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting announcement: {str(e)}")


# PUBLIC ENDPOINTS (new)
@public_router.get("/", response_model=List[AnnouncementSchema])
def get_public_announcements(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(20, ge=1, le=50, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all announcements for public viewing (no authentication required)"""
    try:
        announcements = (
            db.query(Announcement)
            .order_by(Announcement.announced_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )
        return announcements
    except Exception as e:
        logger.error(f"Error fetching public announcements: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching announcements")

@public_router.get("/{announcement_id}", response_model=AnnouncementSchema)
def get_public_announcement(
    announcement_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific announcement by ID for public viewing (no authentication required)"""
    try:
        db_announcement = db.query(Announcement).filter(Announcement.id == announcement_id).first()
        if db_announcement is None:
            raise HTTPException(status_code=404, detail="Announcement not found")
        return db_announcement
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching announcement {announcement_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching announcement")

@public_router.get("/latest/{count}", response_model=List[AnnouncementSchema])
def get_latest_announcements(
    count: int = Path(..., ge=1, le=10, description="Number of latest announcements to return"),
    db: Session = Depends(get_db)
):
    """Get the latest announcements for public viewing (no authentication required)"""
    try:
        announcements = (
            db.query(Announcement)
            .order_by(Announcement.announced_at.desc())
            .limit(count)
            .all()
        )
        return announcements
    except Exception as e:
        logger.error(f"Error fetching latest announcements: {str(e)}")
        raise HTTPException(status_code=500, detail="Error fetching latest announcements")


# For backward compatibility, keep the original router name
router = admin_router