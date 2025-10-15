from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query, Path
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.announcement import Announcement
from app.models.student import student as StudentModel  # Renamed import to avoid conflict
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

# Helper function to generate modern email HTML template
def generate_email_html(title: str, content: str, image_url: Optional[str], admin_name: str) -> str:
    """Generate a modern, international-standard HTML email template with JKUSA branding"""
    
    # JKUSA Color Theme
    PRIMARY_COLOR = "#1a472a"      # Dark Green
    SECONDARY_COLOR = "#2d5f3f"    # Medium Green
    ACCENT_COLOR = "#4a9d5f"       # Light Green
    TEXT_COLOR = "#2c3e50"         # Dark Gray
    LIGHT_BG = "#f8faf9"           # Very Light Green
    WHITE = "#ffffff"
    
    # Image section with responsive design
    image_section = ""
    if image_url:
        image_section = f"""
        <tr>
            <td style="padding: 0;">
                <img src="{image_url}" alt="Announcement Image" 
                     style="width: 100%; max-width: 600px; height: auto; display: block; border-radius: 12px; margin: 24px 0;" />
            </td>
        </tr>
        """
    
    html_template = f"""
    <!DOCTYPE html>
    <html lang="en" xmlns="http://www.w3.org/1999/xhtml" xmlns:o="urn:schemas-microsoft-com:office:office">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="IE=edge">
        <meta name="x-apple-disable-message-reformatting">
        <title>JKUSA Announcement</title>
        <!--[if mso]>
        <style type="text/css">
            body, table, td {{font-family: Arial, Helvetica, sans-serif !important;}}
        </style>
        <![endif]-->
        <style type="text/css">
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            
            body {{
                margin: 0;
                padding: 0;
                background-color: {LIGHT_BG};
                font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
            }}
            table {{
                border-collapse: collapse;
                border-spacing: 0;
            }}
            img {{
                border: 0;
                outline: none;
                text-decoration: none;
                -ms-interpolation-mode: bicubic;
            }}
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
            }}
            @media only screen and (max-width: 600px) {{
                .email-container {{
                    width: 100% !important;
                }}
                .mobile-padding {{
                    padding: 16px !important;
                }}
                .mobile-text {{
                    font-size: 14px !important;
                    line-height: 1.6 !important;
                }}
            }}
        </style>
    </head>
    <body style="margin: 0; padding: 0; background-color: {LIGHT_BG};">
        <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%" style="background-color: {LIGHT_BG};">
            <tr>
                <td style="padding: 40px 20px;">
                    <!-- Main Email Container -->
                    <table role="presentation" cellspacing="0" cellpadding="0" border="0" class="email-container" 
                           style="background-color: {WHITE}; border-radius: 16px; box-shadow: 0 4px 24px rgba(26, 71, 42, 0.08); overflow: hidden; margin: 0 auto;">
                        
                        <!-- Header with Brand -->
                        <tr>
                            <td style="background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, {SECONDARY_COLOR} 100%); padding: 32px 40px; text-align: center;">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                    <tr>
                                        <td style="text-align: center;">
                                            <h1 style="margin: 0; color: {WHITE}; font-size: 28px; font-weight: 700; letter-spacing: -0.5px;">
                                                📢 JKUSA
                                            </h1>
                                            <p style="margin: 8px 0 0 0; color: rgba(255, 255, 255, 0.9); font-size: 14px; font-weight: 500; letter-spacing: 0.5px; text-transform: uppercase;">
                                                Official Announcement
                                            </p>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Main Content -->
                        <tr>
                            <td class="mobile-padding" style="padding: 40px;">
                                <!-- Title -->
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                    <tr>
                                        <td style="padding-bottom: 24px;">
                                            <h2 style="margin: 0; color: {PRIMARY_COLOR}; font-size: 24px; font-weight: 700; line-height: 1.3;">
                                                {title}
                                            </h2>
                                        </td>
                                    </tr>
                                    
                                    <!-- Content Box -->
                                    <tr>
                                        <td style="background-color: {LIGHT_BG}; padding: 24px; border-radius: 12px; border-left: 4px solid {ACCENT_COLOR};">
                                            <p class="mobile-text" style="margin: 0; color: {TEXT_COLOR}; font-size: 16px; line-height: 1.7; white-space: pre-wrap;">
{content}
                                            </p>
                                        </td>
                                    </tr>
                                    
                                    <!-- Image -->
                                    {image_section}
                                    
                                    <!-- Posted By -->
                                    <tr>
                                        <td style="padding-top: 24px; border-top: 1px solid #e8ebe9;">
                                            <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                                <tr>
                                                    <td style="padding: 16px 0;">
                                                        <p style="margin: 0; color: {TEXT_COLOR}; font-size: 14px; font-weight: 600;">
                                                            Posted by:
                                                        </p>
                                                        <p style="margin: 4px 0 0 0; color: {ACCENT_COLOR}; font-size: 16px; font-weight: 600;">
                                                            {admin_name}
                                                        </p>
                                                    </td>
                                                </tr>
                                            </table>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="background-color: {LIGHT_BG}; padding: 32px 40px; text-align: center; border-top: 1px solid #e8ebe9;">
                                <table role="presentation" cellspacing="0" cellpadding="0" border="0" width="100%">
                                    <tr>
                                        <td style="text-align: center;">
                                            <p style="margin: 0 0 16px 0; color: {TEXT_COLOR}; font-size: 16px; font-weight: 600;">
                                                📱 Stay Connected with JKUSA
                                            </p>
                                            <p style="margin: 0; color: #6c757d; font-size: 13px; line-height: 1.6;">
                                                This is an automated message from JKUSA.<br>
                                                Please do not reply directly to this email.
                                            </p>
                                            <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #dee2e6;">
                                                <p style="margin: 0; color: #6c757d; font-size: 12px;">
                                                    © {datetime.now().year} JKUSA. All rights reserved.<br>
                                                    <a href="https://jkusa.org" style="color: {ACCENT_COLOR}; text-decoration: none; font-weight: 600;">
                                                        Visit our website
                                                    </a>
                                                </p>
                                            </div>
                                        </td>
                                    </tr>
                                </table>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    return html_template

# Helper function to send announcement emails
def send_announcement_email(to_email: str, title: str, content: str, image_url: Optional[str], admin_name: str) -> bool:
    """Send announcement email to a student using Zeptomail API with modern HTML template"""
    try:
        url = "https://api.zeptomail.com/v1.1/email"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": "Zoho-enczapikey wSsVR61/q0SmC60rmD2lIOY6yFhdVVv0F0go3VWjv3T8TPHH98dowRDIDFLxHPVMFjI7RWYVp+14zBgI2zJYhol/nl8FACiF9mqRe1U4J3x17qnvhDzCXmpUlRaJKogBxgRrnmZoE8kl+g=="
        }
        
        # Generate modern HTML email
        html_body = generate_email_html(title, content, image_url, admin_name)
        
        payload = {
            "from": {"address": "announcements@jkusa.org"},
            "to": [{"email_address": {"address": to_email, "name": ""}}],
            "subject": f"📢 JKUSA Announcement: {title}",
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
            admin_id=current_admin.id,
            announced_at=datetime.utcnow()
        )
        db.add(db_announcement)
        db.commit()
        db.refresh(db_announcement)
        
        # Get all active students - using renamed StudentModel
        students = db.query(StudentModel).filter(StudentModel.is_active == True).all()
        email_results = []
        
        # Send emails to all active students - using different variable name
        admin_name = f"{current_admin.first_name} {current_admin.last_name}"
        for student_record in students:  # Changed variable name from 'student' to 'student_record'
            success = send_announcement_email(
                to_email=student_record.email,
                title=title,
                content=content,
                image_url=image_url,
                admin_name=admin_name
            )
            email_results.append({
                "email": student_record.email,
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
        
        # Get all active students - using renamed StudentModel
        students = db.query(StudentModel).filter(StudentModel.is_active == True).all()
        email_results = []
        
        # Send emails to all active students - using different variable name
        admin_name = f"{current_admin.first_name} {current_admin.last_name}"
        for student_record in students:  # Changed variable name from 'student' to 'student_record'
            success = send_announcement_email(
                to_email=student_record.email,
                title=title,
                content=content,
                image_url=new_image_url or old_image_url,
                admin_name=admin_name
            )
            email_results.append({
                "email": student_record.email,
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