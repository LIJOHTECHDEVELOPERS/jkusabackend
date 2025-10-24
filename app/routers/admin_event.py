from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.event import Event 
from app.schemas.event import EventCreate, Event as EventSchema
from app.auth.auth import get_current_admin
from app.services.s3_service import s3_service
from datetime import datetime
from typing import List, Optional
import logging
import re
from PIL import Image
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/events", tags=["admin_events"])
public_event_router = APIRouter(prefix="/events", tags=["public_events"])

def generate_slug(title: str, db: Session, event_id: int = None) -> str:
    """Generate a unique slug from the title."""
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    base_slug = slug
    counter = 1
    while True:
        query = db.query(Event).filter(Event.slug == slug)
        if event_id:
            query = query.filter(Event.id != event_id)
        
        if not query.first():
            return slug
        
        slug = f"{base_slug}-{counter}"
        counter += 1

def optimize_and_upload_image(image: UploadFile) -> str:
    """Optimize image and upload to S3 (1200x630 for social media)"""
    try:
        contents = image.file.read()
        img = Image.open(io.BytesIO(contents))
        
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        target_width = 1200
        target_height = 630
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if img_ratio > target_ratio:
            new_height = target_height
            new_width = int(new_height * img_ratio)
        else:
            new_width = target_width
            new_height = int(new_width / img_ratio)
        
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        img = img.crop((left, top, right, bottom))
        
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        optimized_file = type('obj', (object,), {
            'file': output,
            'filename': image.filename,
            'content_type': 'image/jpeg'
        })()
        
        image_url = s3_service.upload_image(optimized_file)
        return image_url
        
    except Exception as e:
        logger.error(f"Error optimizing image: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")

@public_event_router.get("/", response_model=List[EventSchema])
def read_public_events(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all events with pagination (Public access)"""
    logger.debug(f"Accessing public events: skip={skip}, limit={limit}")
    try:
        events = db.query(Event).order_by(Event.start_date.desc()).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(events)} events")
        return events
    except Exception as e:
        logger.error(f"Error fetching public events: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@public_event_router.get("/slug/{slug}", response_model=EventSchema)
def read_public_event_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get a specific event by slug (Public access)"""
    logger.debug(f"Fetching public event by slug: {slug}")
    try:
        db_event = db.query(Event).filter(Event.slug == slug).first()
        if db_event is None:
            logger.warning(f"Event with slug {slug} not found")
            raise HTTPException(status_code=404, detail="Event not found")
        logger.info(f"Retrieved event with slug: {slug}")
        return db_event
    except Exception as e:
        logger.error(f"Error fetching event by slug {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@public_event_router.get("/{event_id}", response_model=EventSchema)
def read_public_event(
    event_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific event by ID (Public access)"""
    logger.debug(f"Fetching public event ID: {event_id}")
    try:
        db_event = db.query(Event).filter(Event.id == event_id).first()
        if db_event is None:
            logger.warning(f"Event ID {event_id} not found")
            raise HTTPException(status_code=404, detail="Event not found")
        logger.info(f"Retrieved event ID: {event_id}")
        return db_event
    except Exception as e:
        logger.error(f"Error fetching event ID {event_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=EventSchema)
async def create_event(
    title: str = Form(..., min_length=1, max_length=200),
    description: str = Form(..., min_length=1),
    start_date: datetime = Form(...),
    end_date: Optional[datetime] = Form(None),
    location: str = Form(..., min_length=1),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Create a new event with optional end_date for multi-day events (Admin only)"""
    logger.debug(f"Creating event by admin: {current_admin.username}")
    
    image_url = None
    try:
        # Validate dates
        if end_date and end_date < start_date:
            logger.error(f"Invalid date range: end_date ({end_date}) before start_date ({start_date})")
            raise HTTPException(status_code=400, detail="end_date must be equal to or after start_date")
        
        # Validate image if provided
        if image:
            if not image.content_type.startswith('image/'):
                logger.error(f"Invalid file type: {image.content_type}")
                raise HTTPException(status_code=400, detail="File must be an image")
            if image.size > 5 * 1024 * 1024:
                logger.error(f"Image too large: {image.size} bytes")
                raise HTTPException(status_code=400, detail="Image must be less than 5MB")
            
            logger.debug(f"Optimizing and uploading image: {image.filename}")
            image_url = optimize_and_upload_image(image)
            if not image_url:
                logger.error("Failed to upload optimized image")
                raise HTTPException(status_code=500, detail="Failed to upload image")
            logger.debug(f"Image uploaded successfully: {image_url}")

        slug = generate_slug(title, db)
        logger.debug(f"Generated slug: {slug}")

        db_event = Event(
            title=title.strip(),
            description=description.strip(),
            start_date=start_date,
            end_date=end_date,
            location=location.strip(),
            image_url=image_url,
            slug=slug
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        duration_str = f"{start_date.date()} to {end_date.date()}" if end_date else str(start_date.date())
        logger.info(f"Admin {current_admin.username} created event ID {db_event.id}: {title} ({duration_str}, slug: {slug})")
        return db_event
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        if image_url:
            try:
                s3_service.delete_image(image_url)
                logger.debug(f"Cleaned up uploaded image: {image_url}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup uploaded image: {cleanup_error}")
        
        logger.error(f"Error creating event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating event: {str(e)}")

@router.get("/{event_id}", response_model=EventSchema)
def read_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get a specific event by ID (Admin only)"""
    logger.debug(f"Admin {current_admin.username} fetching event ID: {event_id}")
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        logger.warning(f"Event ID {event_id} not found")
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event

@router.get("/", response_model=List[EventSchema])
def read_events(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get all events with pagination (Admin only)"""
    logger.debug(f"Admin {current_admin.username} fetching events: skip={skip}, limit={limit}")
    events = db.query(Event).order_by(Event.start_date.desc()).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(events)} events for admin")
    return events

@router.put("/{event_id}", response_model=EventSchema)
async def update_event(
    event_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    start_date: Optional[datetime] = Form(None),
    end_date: Optional[datetime] = Form(None),
    location: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    remove_image: Optional[str] = Form("false"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Update an existing event with multi-day support (Admin only)"""
    logger.debug(f"Updating event ID: {event_id} by admin: {current_admin.username}")
    
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        logger.warning(f"Event ID {event_id} not found")
        raise HTTPException(status_code=404, detail="Event not found")

    logger.debug(f"Current event state: title={db_event.title}, start_date={db_event.start_date}, end_date={db_event.end_date}")

    new_image_url = None
    old_image_url = db_event.image_url
    updated = False
    changes_made = []
    
    try:
        if image:
            if not image.content_type.startswith('image/'):
                logger.error(f"Invalid file type: {image.content_type}")
                raise HTTPException(status_code=400, detail="File must be an image")
            if image.size > 5 * 1024 * 1024:
                logger.error(f"Image too large: {image.size} bytes")
                raise HTTPException(status_code=400, detail="Image must be less than 5MB")
        
        if title is not None:
            title_trimmed = title.strip()
            if title_trimmed != db_event.title:
                if len(title_trimmed) < 1 or len(title_trimmed) > 200:
                    raise HTTPException(status_code=400, detail="Title must be 1-200 characters")
                
                logger.debug(f"Title changed: '{db_event.title}' -> '{title_trimmed}'")
                db_event.title = title_trimmed
                new_slug = generate_slug(title_trimmed, db, event_id)
                db_event.slug = new_slug
                updated = True
                changes_made.extend(["title", "slug"])

        if description is not None:
            description_trimmed = description.strip()
            if description_trimmed != db_event.description:
                if len(description_trimmed) < 1:
                    raise HTTPException(status_code=400, detail="Description must not be empty")
                
                db_event.description = description_trimmed
                updated = True
                changes_made.append("description")

        if start_date is not None:
            if start_date != db_event.start_date:
                logger.debug(f"Start date changed: '{db_event.start_date}' -> '{start_date}'")
                db_event.start_date = start_date
                updated = True
                changes_made.append("start_date")

        if end_date is not None:
            if end_date != db_event.end_date:
                logger.debug(f"End date changed: '{db_event.end_date}' -> '{end_date}'")
                db_event.end_date = end_date
                updated = True
                changes_made.append("end_date")
        
        # Handle end_date removal (convert multi-day to single-day)
        if end_date is None and "end_date" not in str(Form(...)):
            # Only remove end_date if explicitly clearing it
            if db_event.end_date is not None and remove_image != "remove_end_date":
                pass  # Only update if explicitly sent

        if location is not None:
            location_trimmed = location.strip()
            if location_trimmed != db_event.location:
                if len(location_trimmed) < 1:
                    raise HTTPException(status_code=400, detail="Location must not be empty")
                
                db_event.location = location_trimmed
                updated = True
                changes_made.append("location")

        # Validate date range
        final_start = db_event.start_date
        final_end = db_event.end_date
        if final_end and final_end < final_start:
            raise HTTPException(status_code=400, detail="end_date must be equal to or after start_date")

        if image:
            logger.debug(f"Uploading new image: {image.filename}")
            new_image_url = optimize_and_upload_image(image)
            if not new_image_url:
                raise HTTPException(status_code=500, detail="Failed to upload image")
            
            db_event.image_url = new_image_url
            updated = True
            changes_made.append("image")
            
        elif remove_image == "true" and db_event.image_url:
            logger.debug(f"Removing image: {db_event.image_url}")
            db_event.image_url = None
            updated = True
            changes_made.append("removed_image")

        if not updated:
            logger.info("No changes detected")
            return db_event

        db.commit()
        db.refresh(db_event)
        
        if new_image_url and old_image_url:
            try:
                s3_service.delete_image(old_image_url)
                logger.debug(f"Deleted old image: {old_image_url}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete old image: {cleanup_error}")
        
        if remove_image == "true" and old_image_url:
            try:
                s3_service.delete_image(old_image_url)
                logger.debug(f"Deleted removed image: {old_image_url}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete removed image: {cleanup_error}")
        
        logger.info(f"Admin {current_admin.username} updated event ID {event_id}. Changes: {', '.join(changes_made)}")
        return db_event
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        if new_image_url:
            try:
                s3_service.delete_image(new_image_url)
                logger.debug(f"Cleaned up uploaded image: {new_image_url}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup uploaded image: {cleanup_error}")
        
        logger.error(f"Error updating event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating event: {str(e)}")

@router.delete("/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Delete an event (Admin only)"""
    logger.debug(f"Deleting event ID: {event_id} by admin: {current_admin.username}")
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        logger.warning(f"Event ID {event_id} not found")
        raise HTTPException(status_code=404, detail="Event not found")

    image_url = db_event.image_url
    
    try:
        db.delete(db_event)
        db.commit()
        
        if image_url:
            try:
                s3_service.delete_image(image_url)
                logger.debug(f"Deleted image: {image_url}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete image from S3: {cleanup_error}")
        
        logger.info(f"Admin {current_admin.username} deleted event ID {event_id}")
        return {"detail": "Event deleted"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")