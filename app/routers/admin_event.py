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
        # Read and open the image
        contents = image.file.read()
        img = Image.open(io.BytesIO(contents))
        
        # Convert to RGB if necessary (handles PNG with transparency)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Calculate dimensions to maintain aspect ratio and crop to 1200x630
        target_width = 1200
        target_height = 630
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if img_ratio > target_ratio:
            # Image is wider, scale by height
            new_height = target_height
            new_width = int(new_height * img_ratio)
        else:
            # Image is taller, scale by width
            new_width = target_width
            new_height = int(new_width / img_ratio)
        
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to exact dimensions (center crop)
        left = (new_width - target_width) // 2
        top = (new_height - target_height) // 2
        right = left + target_width
        bottom = top + target_height
        img = img.crop((left, top, right, bottom))
        
        # Compress and save to bytes
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)
        
        # Create a new UploadFile-like object with optimized image
        optimized_file = type('obj', (object,), {
            'file': output,
            'filename': image.filename,
            'content_type': 'image/jpeg'
        })()
        
        # Upload to S3
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
        events = db.query(Event).order_by(Event.date.desc()).offset(skip).limit(limit).all()
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
    date: datetime = Form(...),
    location: str = Form(..., min_length=1),
    image: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Create a new event with optimized image (Admin only)"""
    logger.debug(f"Creating event by admin: {current_admin.username}")
    
    image_url = None
    try:
        # Validate image if provided
        if image:
            if not image.content_type.startswith('image/'):
                logger.error(f"Invalid file type: {image.content_type}")
                raise HTTPException(status_code=400, detail="File must be an image")
            if image.size > 5 * 1024 * 1024:
                logger.error(f"Image too large: {image.size} bytes")
                raise HTTPException(status_code=400, detail="Image must be less than 5MB")
            
            # Optimize and upload image
            logger.debug(f"Optimizing and uploading image: {image.filename}")
            image_url = optimize_and_upload_image(image)
            if not image_url:
                logger.error("Failed to upload optimized image")
                raise HTTPException(status_code=500, detail="Failed to upload image")
            logger.debug(f"Image uploaded successfully: {image_url}")

        # Generate unique slug
        slug = generate_slug(title, db)
        logger.debug(f"Generated slug: {slug}")

        # Create event
        db_event = Event(
            title=title.strip(),
            description=description.strip(),
            date=date,
            location=location.strip(),
            image_url=image_url,
            slug=slug
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        logger.info(f"Admin {current_admin.username} created event ID {db_event.id}: {title} (slug: {slug})")
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
    events = db.query(Event).order_by(Event.date.desc()).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(events)} events for admin")
    return events

@router.put("/{event_id}", response_model=EventSchema)
async def update_event(
    event_id: int,
    title: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    date: Optional[datetime] = Form(None),
    location: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    remove_image: Optional[str] = Form("false"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Update an existing event with enhanced image handling (Admin only)"""
    logger.debug(f"Updating event ID: {event_id} by admin: {current_admin.username}")
    logger.debug(f"Received parameters:")
    logger.debug(f"  - title: {title}")
    logger.debug(f"  - description: {description[:50] + '...' if description and len(description) > 50 else description}")
    logger.debug(f"  - date: {date}")
    logger.debug(f"  - location: {location}")
    logger.debug(f"  - image: {image.filename if image else None}")
    logger.debug(f"  - remove_image: {remove_image}")
    
    # Fetch the existing event
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        logger.warning(f"Event ID {event_id} not found")
        raise HTTPException(status_code=404, detail="Event not found")

    # Log current event state
    logger.debug(f"Current event state:")
    logger.debug(f"  - title: {db_event.title}")
    logger.debug(f"  - slug: {db_event.slug}")
    logger.debug(f"  - description: {db_event.description[:50] + '...' if len(db_event.description) > 50 else db_event.description}")
    logger.debug(f"  - date: {db_event.date}")
    logger.debug(f"  - location: {db_event.location}")
    logger.debug(f"  - image_url: {db_event.image_url}")

    new_image_url = None
    old_image_url = db_event.image_url
    updated = False
    changes_made = []
    
    try:
        # Validate new image if provided
        if image:
            if not image.content_type.startswith('image/'):
                logger.error(f"Invalid file type: {image.content_type}")
                raise HTTPException(status_code=400, detail="File must be an image")
            if image.size > 5 * 1024 * 1024:
                logger.error(f"Image too large: {image.size} bytes")
                raise HTTPException(status_code=400, detail="Image must be less than 5MB")
        
        # Update title and regenerate slug if changed
        if title is not None:
            title_trimmed = title.strip()
            if title_trimmed != db_event.title:
                if len(title_trimmed) < 1 or len(title_trimmed) > 200:
                    logger.error(f"Invalid title length: {len(title_trimmed)}")
                    raise HTTPException(status_code=400, detail="Title must be 1-200 characters")
                
                logger.debug(f"Title change detected: '{db_event.title}' -> '{title_trimmed}'")
                db_event.title = title_trimmed
                
                # Regenerate slug when title changes
                new_slug = generate_slug(title_trimmed, db, event_id)
                logger.debug(f"Slug updated: '{db_event.slug}' -> '{new_slug}'")
                db_event.slug = new_slug
                
                updated = True
                changes_made.append("title")
                changes_made.append("slug")
            else:
                logger.debug("Title unchanged")

        # Update description
        if description is not None:
            description_trimmed = description.strip()
            if description_trimmed != db_event.description:
                if len(description_trimmed) < 1:
                    logger.error("Description cannot be empty")
                    raise HTTPException(status_code=400, detail="Description must not be empty")
                
                logger.debug(f"Description change detected (length: {len(db_event.description)} -> {len(description_trimmed)})")
                db_event.description = description_trimmed
                updated = True
                changes_made.append("description")
            else:
                logger.debug("Description unchanged")

        # Update date
        if date is not None:
            if date != db_event.date:
                logger.debug(f"Date change detected: '{db_event.date}' -> '{date}'")
                db_event.date = date
                updated = True
                changes_made.append("date")
            else:
                logger.debug("Date unchanged")

        # Update location
        if location is not None:
            location_trimmed = location.strip()
            if location_trimmed != db_event.location:
                if len(location_trimmed) < 1:
                    logger.error("Location cannot be empty")
                    raise HTTPException(status_code=400, detail="Location must not be empty")
                
                logger.debug(f"Location change detected: '{db_event.location}' -> '{location_trimmed}'")
                db_event.location = location_trimmed
                updated = True
                changes_made.append("location")
            else:
                logger.debug("Location unchanged")

        # Handle image update or removal
        if image:
            # Optimize and upload new image
            logger.debug(f"Optimizing and uploading new image: {image.filename}")
            new_image_url = optimize_and_upload_image(image)
            if not new_image_url:
                logger.error("Failed to upload optimized image")
                raise HTTPException(status_code=500, detail="Failed to upload image")
            
            logger.debug(f"Image change detected: '{db_event.image_url}' -> '{new_image_url}'")
            db_event.image_url = new_image_url
            updated = True
            changes_made.append("image")
            
        elif remove_image == "true" and db_event.image_url:
            logger.debug(f"Removing existing image: {db_event.image_url}")
            db_event.image_url = None
            updated = True
            changes_made.append("removed_image")

        # Log update summary
        logger.debug(f"Update summary:")
        logger.debug(f"  - Changes detected: {updated}")
        logger.debug(f"  - Fields changed: {changes_made}")

        # Handle the case when no changes are detected
        if not updated:
            logger.info("No changes detected - returning existing event without error")
            return db_event

        # Commit changes
        db.commit()
        db.refresh(db_event)
        
        # Delete old image if new one was uploaded successfully
        if new_image_url and old_image_url:
            try:
                s3_service.delete_image(old_image_url)
                logger.debug(f"Deleted old image: {old_image_url}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete old image: {cleanup_error}")
        
        # Delete old image if removal was requested
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
                logger.debug(f"Cleaned up uploaded image after error: {new_image_url}")
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