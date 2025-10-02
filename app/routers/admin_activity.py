from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.database import get_db
from app.models.activity import Activity as ActivityModel
from app.schemas.activity import Activity, ActivityCreate, ActivityUpdate
from app.models.admin import Admin
from app.services.s3_service import s3_service
from datetime import datetime
from typing import Optional
import logging

# FIXED: Import get_current_admin from the correct location
from app.auth.auth import get_current_admin

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Routers
router = APIRouter(prefix="/admin/activities", tags=["admin_activities"])
public_activity_router = APIRouter(prefix="/activities", tags=["public_activities"])

@router.post("/", response_model=Activity)
async def create_activity(
    title: str = Form(...),
    description: str = Form(...),
    start_datetime: str = Form(...),
    end_datetime: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    featured_image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """Create a new activity with optional featured image."""
    logger.debug(f"Creating activity by user: {current_user.id}")
    
    # Parse start_datetime
    try:
        parsed_start = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
        parsed_start = parsed_start.replace(second=0, microsecond=0)
    except ValueError as e:
        logger.error(f"Invalid start_datetime format: {e}")
        raise HTTPException(status_code=400, detail="Invalid start_datetime format. Use ISO 8601")

    # Parse end_datetime if provided
    parsed_end = None
    if end_datetime:
        try:
            parsed_end = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
            parsed_end = parsed_end.replace(second=0, microsecond=0)
            if parsed_end <= parsed_start:
                raise HTTPException(status_code=400, detail="end_datetime must be after start_datetime")
        except ValueError as e:
            logger.error(f"Invalid end_datetime format: {e}")
            raise HTTPException(status_code=400, detail="Invalid end_datetime format. Use ISO 8601")

    # Validate and upload featured image
    featured_image_url = None
    if featured_image:
        if not featured_image.content_type.startswith('image/'):
            logger.error(f"Invalid file type: {featured_image.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")
        if featured_image.size > 5 * 1024 * 1024:
            logger.error(f"Image too large: {featured_image.size} bytes")
            raise HTTPException(status_code=400, detail="Image must be less than 5MB")
        featured_image_url = s3_service.upload_image(featured_image)
        if not featured_image_url:
            logger.error("Failed to upload image to S3")
            raise HTTPException(status_code=500, detail="Failed to upload image")
    
    # Create activity
    db_activity = ActivityModel(
        title=title.strip(),
        description=description.strip(),
        start_datetime=parsed_start,
        end_datetime=parsed_end,
        location=location.strip() if location else None,
        featured_image_url=featured_image_url,
        published_at=datetime.utcnow().replace(microsecond=0),
        publisher_id=current_user.id
    )
    
    try:
        db.add(db_activity)
        db.commit()
        db.refresh(db_activity)
        logger.info(f"Created activity ID {db_activity.id}: {db_activity.title}")
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {e}")
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    
    return db_activity

@router.get("/", response_model=list[Activity])
async def read_activities_list(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """Get list of activities (admin only)."""
    logger.debug(f"Fetching activities list: skip={skip}, limit={limit}")
    return db.query(ActivityModel).offset(skip).limit(limit).all()

@public_activity_router.get("/", response_model=list[Activity])
async def read_public_activities_list(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """Get list of activities (public access), ordered by start_datetime ascending."""
    logger.debug(f"Fetching public activities list: skip={skip}, limit={limit}")
    return db.query(ActivityModel).order_by(ActivityModel.start_datetime.asc()).offset(skip).limit(limit).all()

@router.get("/{activity_id}", response_model=Activity)
async def read_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """Get a specific activity (admin only)."""
    logger.debug(f"Fetching activity ID: {activity_id}")
    db_activity = db.query(ActivityModel).filter(ActivityModel.id == activity_id).first()
    if db_activity is None:
        logger.warning(f"Activity ID {activity_id} not found")
        raise HTTPException(status_code=404, detail="Activity not found")
    return db_activity

@public_activity_router.get("/{activity_id}", response_model=Activity)
async def read_public_activity(
    activity_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific activity (public access)."""
    logger.debug(f"Fetching public activity ID: {activity_id}")
    db_activity = db.query(ActivityModel).filter(ActivityModel.id == activity_id).first()
    if db_activity is None:
        logger.warning(f"Activity ID {activity_id} not found")
        raise HTTPException(status_code=404, detail="Activity not found")
    return db_activity

@router.put("/{activity_id}", response_model=Activity)
async def update_activity(
    activity_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    start_datetime: Optional[str] = Form(None),
    end_datetime: Optional[str] = Form(None),
    location: Optional[str] = Form(None),
    featured_image: Optional[UploadFile] = File(None),
    remove_image: Optional[str] = Form("false"),
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """Update an activity."""
    logger.debug(f"Updating activity ID: {activity_id} by user: {current_user.id}")
    logger.debug(f"Received parameters: title={title}, description={description[:50] + '...' if description and len(description) > 50 else description}, "
                 f"start_datetime={start_datetime}, end_datetime={end_datetime}, location={location}, "
                 f"featured_image={featured_image.filename if featured_image else None}, remove_image={remove_image}")

    # Fetch the existing activity
    db_activity = db.query(ActivityModel).filter(ActivityModel.id == activity_id).first()
    if db_activity is None:
        logger.warning(f"Activity ID {activity_id} not found")
        raise HTTPException(status_code=404, detail="Activity not found")

    logger.debug(f"Current activity state: title={db_activity.title}, "
                 f"description={db_activity.description[:50] + '...' if len(db_activity.description) > 50 else db_activity.description}, "
                 f"start_datetime={db_activity.start_datetime}, end_datetime={db_activity.end_datetime}, "
                 f"location={db_activity.location}, featured_image_url={db_activity.featured_image_url}")

    updated = False
    changes_made = []

    # Update title
    if title is not None:
        title_trimmed = title.strip()
        if title_trimmed != db_activity.title:
            if len(title_trimmed) < 10 or len(title_trimmed) > 200:
                logger.error(f"Invalid title length: {len(title_trimmed)}")
                raise HTTPException(status_code=400, detail="Title must be 10-200 characters")
            logger.debug(f"Title changed: '{db_activity.title}' -> '{title_trimmed}'")
            db_activity.title = title_trimmed
            updated = True
            changes_made.append("title")
        else:
            logger.debug("Title unchanged")

    # Update description
    if description is not None:
        description_trimmed = description.strip()
        if description_trimmed != db_activity.description:
            if len(description_trimmed) < 50:
                logger.error(f"Invalid description length: {len(description_trimmed)}")
                raise HTTPException(status_code=400, detail="Description must be at least 50 characters")
            logger.debug(f"Description changed (length: {len(db_activity.description)} -> {len(description_trimmed)})")
            db_activity.description = description_trimmed
            updated = True
            changes_made.append("description")
        else:
            logger.debug("Description unchanged")

    # Update start_datetime
    if start_datetime is not None:
        try:
            parsed_start = datetime.fromisoformat(start_datetime.replace('Z', '+00:00'))
            parsed_start = parsed_start.replace(second=0, microsecond=0)
            existing_start = db_activity.start_datetime.replace(second=0, microsecond=0)
            if parsed_start != existing_start:
                logger.debug(f"Start datetime changed: '{existing_start}' -> '{parsed_start}'")
                db_activity.start_datetime = parsed_start
                updated = True
                changes_made.append("start_datetime")
            else:
                logger.debug("Start datetime unchanged")
        except ValueError as e:
            logger.error(f"Invalid start_datetime format: {e}")
            raise HTTPException(status_code=400, detail="Invalid start_datetime format. Use ISO 8601")

    # Update end_datetime
    if end_datetime is not None:
        try:
            if end_datetime == "":
                if db_activity.end_datetime is not None:
                    logger.debug(f"Removing end_datetime: '{db_activity.end_datetime}' -> None")
                    db_activity.end_datetime = None
                    updated = True
                    changes_made.append("end_datetime")
            else:
                parsed_end = datetime.fromisoformat(end_datetime.replace('Z', '+00:00'))
                parsed_end = parsed_end.replace(second=0, microsecond=0)
                existing_end = db_activity.end_datetime.replace(second=0, microsecond=0) if db_activity.end_datetime else None
                if parsed_end != existing_end:
                    if parsed_end <= db_activity.start_datetime:
                        raise HTTPException(status_code=400, detail="end_datetime must be after start_datetime")
                    logger.debug(f"End datetime changed: '{existing_end}' -> '{parsed_end}'")
                    db_activity.end_datetime = parsed_end
                    updated = True
                    changes_made.append("end_datetime")
                else:
                    logger.debug("End datetime unchanged")
        except ValueError as e:
            logger.error(f"Invalid end_datetime format: {e}")
            raise HTTPException(status_code=400, detail="Invalid end_datetime format. Use ISO 8601")

    # Update location
    if location is not None:
        location_trimmed = location.strip() if location else None
        if location_trimmed != db_activity.location:
            logger.debug(f"Location changed: '{db_activity.location}' -> '{location_trimmed}'")
            db_activity.location = location_trimmed
            updated = True
            changes_made.append("location")
        else:
            logger.debug("Location unchanged")

    # Handle image update or removal
    if featured_image:
        if not featured_image.content_type.startswith('image/'):
            logger.error(f"Invalid file type: {featured_image.content_type}")
            raise HTTPException(status_code=400, detail="File must be an image")
        if featured_image.size > 5 * 1024 * 1024:
            logger.error(f"Image too large: {featured_image.size} bytes")
            raise HTTPException(status_code=400, detail="Image must be less than 5MB")
        
        if db_activity.featured_image_url:
            logger.debug(f"Deleting old image: {db_activity.featured_image_url}")
            s3_service.delete_image(db_activity.featured_image_url)
        
        new_image_url = s3_service.upload_image(featured_image)
        if not new_image_url:
            logger.error("Failed to upload image to S3")
            raise HTTPException(status_code=500, detail="Failed to upload image")
        
        logger.debug(f"Image changed: '{db_activity.featured_image_url}' -> '{new_image_url}'")
        db_activity.featured_image_url = new_image_url
        updated = True
        changes_made.append("featured_image")
        
    elif remove_image == "true" and db_activity.featured_image_url:
        logger.debug(f"Removing existing image: {db_activity.featured_image_url}")
        s3_service.delete_image(db_activity.featured_image_url)
        db_activity.featured_image_url = None
        updated = True
        changes_made.append("removed_image")

    logger.debug(f"Update summary: Changes detected: {updated}, Fields changed: {changes_made}")

    if not updated:
        logger.info("No changes detected - returning existing activity")
        return db_activity

    try:
        db.commit()
        db.refresh(db_activity)
        logger.info(f"Successfully updated activity ID {activity_id}. Changes: {', '.join(changes_made)}")
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {e}")
        raise HTTPException(status_code=400, detail=f"Database error: {str(e)}")
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during commit: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

    return db_activity

@router.delete("/{activity_id}")
async def delete_activity(
    activity_id: int,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """Delete an activity."""
    logger.debug(f"Deleting activity ID: {activity_id} by user: {current_user.id}")
    db_activity = db.query(ActivityModel).filter(ActivityModel.id == activity_id).first()
    if db_activity is None:
        logger.warning(f"Activity ID {activity_id} not found")
        raise HTTPException(status_code=404, detail="Activity not found")
    
    if db_activity.featured_image_url:
        logger.debug(f"Deleting image: {db_activity.featured_image_url}")
        s3_service.delete_image(db_activity.featured_image_url)
    
    db.delete(db_activity)
    db.commit()
    logger.info(f"Deleted activity ID: {activity_id}")
    return {"detail": "Activity deleted"}

@router.get("/my/activities", response_model=list[Activity])
async def get_my_activities(
    skip: int = 0,
    limit: int = 10,
    db: Session = Depends(get_db),
    current_user: Admin = Depends(get_current_admin)
):
    """Get activities published by the current admin."""
    logger.debug(f"Fetching activities for user: {current_user.id}, skip={skip}, limit={limit}")
    return db.query(ActivityModel).filter(ActivityModel.publisher_id == current_user.id).offset(skip).limit(limit).all()