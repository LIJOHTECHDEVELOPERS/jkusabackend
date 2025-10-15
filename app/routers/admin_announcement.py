from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.announcement import Announcement
from app.models.student import student  # Added student model import
from app.schemas.announcement import Announcement as AnnouncementSchema, AnnouncementCreate
from app.auth.auth import get_current_admin
from app.services.s3_service import s3_service
from datetime import datetime
import logging
import requests

logger = logging.getLogger(__name__)

# Admin router for announcement management
admin_router = APIRouter(prefix="/admin/announcements", tags=["admin_announcements"])

# Public router for viewing announcements
public_router = APIRouter(prefix="/announcements", tags=["public_announcements"])

# Helper function to send announcement emails
def send_announcement_email(to_email: str, title: str, content: str, image_url: Optional[str], admin_name: str) -> bool:
    """Send announcement email to a student using Zeptomail API"""
    try:
        url = "https://api.zeptomail.com/v1.1/email"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Zoho-enczapikey wSsVR61/q0SmC60rmD2lIOY6yFhdVVv0F0go3VWjv3T8TPHH98dowRDIDFLxHPVMFjI7RWYVp+14zBgI2zJYhol/nl8FACiF9mqRe1U4J3x17qnvhDzCXmpUlRaJKogBxgRrnmZoE8kl+g=="
        }
        
        # Modern HTML email template
        image_html = f'<img src="{image_url}" alt="Announcement Image" style="max-width: 100%; height: auto; margin: 20px 0; border-radius: 8px;">' if image_url else ''
        html_body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="background-color: #f8f9fa; padding: 20px; border-radius: 8px;">
                <h2 style="color: #333; margin-bottom: 20px;">{title}</h2>
                <div style="background-color: white; padding: 15px; border-radius: 4px; border: 1px solid #dee2e6;">
                    <p style="color: #333; line-height: 1.6;">{content}</p>
                    {image_html}
                </div>
                <p style="color: #666; margin-top: 20px;">Posted by: {admin_name}</p>
                <p style="color: #666; font-size: 12px; margin-top: 20px;">
                    This is an automated message from JKUSA. Please do not reply directly to this email.
                </p>
            </div>
        </div>
        """
        
        payload = {
            "from": {"address": "announcements@jkusa.org"},
            "to": [{"email_address": {"address": to_email, "name": ""}}],
            "subject": f"JKUSA Announcement: {title}",
            "htmlbody": html_body
        }
        
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {str(e)}")
        return False

# ADMIN ENDPOINTS
@admin_router.post("/", response_model=dict)
async def create_announcement(
    title: str = Form(..., min_length=1, max_length=200),
    content: str = Form(..., min_length=1),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Create a new announcement and send email notifications to all active students (Admin only)"""
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
            announced_at=datetime.utcnow(),
            admin_id=current_admin.id  # Store admin ID
        )
        db.add(db_announcement)
        db.commit()
        db.refresh(db_announcement)
        
        # Get all active students
        students = db.query(student).filter(student.is_active == True).all()
        email_results = []
        
        # Send emails to all active students
        admin_name = f"{current_admin.first_name} {current_admin.last_name}"
        for student in students:
            success = send_announcement_email(
                to_email=student.email,
                title=title,
                content=content,
                image_url=image_url,
                admin_name=admin_name
            )
            email_results.append({
                "email": student.email,
                "success": success
            })
        
        # Count successful and failed emails
        successful_emails = sum(1 for result in email_results if result["success"])
        failed_emails = len(email_results) - successful_emails
        
        logger.info(f"Admin {current_admin.username} created announcement ID {db_announcement.id}: {title}. "
                   f"Sent to {successful_emails}/{len(students)} students successfully")
        
        return {
            "success": True,
            "message": f"Announcement created and sent to {successful_emails}/{len(students)} students",
            "code": "ANNOUNCEMENT_CREATED",
            "data": {
                "id": db_announcement.id,
                "title": db_announcement.title,
                "content": db_announcement.content,
                "image_url": db_announcement.image_url,
                "announced_at": db_announcement.announced_at,
                "admin_id": db_announcement.admin_id
            },
            "email_stats": {
                "total": len(students),
                "successful": successful_emails,
                "failed": failed_emails
            }
        }
        
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
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": f"Error creating announcement: {str(e)}",
            "code": "SERVER_ERROR"
        })

@admin_router.put("/{announcement_id}", response_model=dict)
async def update_announcement(
    announcement_id: int,
    title: str = Form(..., min_length=1, max_length=200),
    content: str = Form(..., min_length=1),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Update an existing announcement and send email notifications to all active students (Admin only)"""
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
        db_announcement.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(db_announcement)
        
        # Get all active students
        students = db.query(student).filter(student.is_active == True).all()
        email_results = []
        
        # Send emails to all active students
        admin_name = f"{current_admin.first_name} {current_admin.last_name}"
        for student in students:
            success = send_announcement_email(
                to_email=student.email,
                title=title,
                content=content,
                image_url=new_image_url or old_image_url,
                admin_name=admin_name
            )
            email_results.append({
                "email": student.email,
                "success": success
            })
        
        # Count successful and failed emails
        successful_emails = sum(1 for result in email_results if result["success"])
        failed_emails = len(email_results) - successful_emails
        
        # Delete old image after successful update
        if new_image_url and old_image_url:
            try:
                s3_service.delete_image(old_image_url)
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete old image: {cleanup_error}")
        
        logger.info(f"Admin {current_admin.username} updated announcement ID {announcement_id}. "
                   f"Sent to {successful_emails}/{len(students)} students successfully")
        
        return {
            "success": True,
            "message": f"Announcement updated and sent to {successful_emails}/{len(students)} students",
            "code": "ANNOUNCEMENT_UPDATED",
            "data": {
                "id": db_announcement.id,
                "title": db_announcement.title,
                "content": db_announcement.content,
                "image_url": db_announcement.image_url,
                "announced_at": db_announcement.announced_at,
                "updated_at": db_announcement.updated_at,
                "admin_id": db_announcement.admin_id
            },
            "email_stats": {
                "total": len(students),
                "successful": successful_emails,
                "failed": failed_emails
            }
        }
        
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
        raise HTTPException(status_code=500, detail={
            "success": False,
            "message": f"Error updating announcement: {str(e)}",
            "code": "SERVER_ERROR"
        })

# [Rest of the endpoints remain unchanged]

@admin_router.get("/{announcement_id}", response_model=AnnouncementSchema)
def read_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
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
    current_admin=Depends(get_current_admin)
):
    """Get all announcements with pagination (Admin only)"""
    announcements = db.query(Announcement).order_by(Announcement.announced_at.desc()).offset(skip).limit(limit).all()
    return announcements

@admin_router.delete("/{announcement_id}")
def delete_announcement(
    announcement_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
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

# For backward compatibility
router = admin_router