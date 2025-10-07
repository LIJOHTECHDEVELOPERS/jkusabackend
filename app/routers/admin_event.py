from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.event import Event 
from app.schemas.event import EventCreate, Event as EventSchema
from app.auth.auth import get_current_admin
from app.services.s3_service import s3_service
from datetime import datetime
from typing import List
import logging
import re

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/events", tags=["admin_events"])
public_event_router = APIRouter(prefix="/events", tags=["public_events"])

def generate_slug(title: str, db: Session, event_id: int = None) -> str:
    """Generate a unique slug from the title."""
    slug = re.sub(r'[^a-z0-9]+', '-', title.lower()).strip('-')
    base_slug = slug
    counter = 1
    while db.query(Event).filter(Event.slug == slug, Event.id != event_id).first():
        slug = f"{base_slug}-{counter}"
        counter += 1
    return slug

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
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Create a new event (Admin only)"""
    image_url = None
    try:
        if image:
            if not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            if image.size > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
        
        if image:
            image_url = s3_service.upload_image(image)
            if not image_url:
                raise HTTPException(status_code=500, detail="Failed to upload image")

        slug = generate_slug(title, db)

        db_event = Event(
            title=title,
            description=description,
            date=date,
            location=location,
            image_url=image_url,
            slug=slug
        )
        db.add(db_event)
        db.commit()
        db.refresh(db_event)
        
        logger.info(f"Admin {current_admin.username} created event: {title} with slug {slug}")
        return db_event
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        if image_url:
            try:
                s3_service.delete_image(image_url)
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
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
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
    events = db.query(Event).order_by(Event.date.desc()).offset(skip).limit(limit).all()
    return events

@router.put("/{event_id}", response_model=EventSchema)
async def update_event(
    event_id: int,
    title: str = Form(..., min_length=1, max_length=200),
    description: str = Form(..., min_length=1),
    date: datetime = Form(...),
    location: str = Form(..., min_length=1),
    image: UploadFile = File(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Update an existing event (Admin only)"""
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    new_image_url = None
    old_image_url = db_event.image_url
    
    try:
        if image:
            if not image.content_type.startswith('image/'):
                raise HTTPException(status_code=400, detail="File must be an image")
            if image.size > 5 * 1024 * 1024:
                raise HTTPException(status_code=400, detail="Image too large (max 5MB)")
        
        if image:
            new_image_url = s3_service.upload_image(image)
            if not new_image_url:
                raise HTTPException(status_code=500, detail="Failed to upload image")

        # Regenerate slug if title changes
        if title != db_event.title:
            db_event.slug = generate_slug(title, db, event_id)

        db_event.title = title
        db_event.description = description
        db_event.date = date
        db_event.location = location
        if new_image_url:
            db_event.image_url = new_image_url
        
        db.commit()
        db.refresh(db_event)
        
        if new_image_url and old_image_url:
            try:
                s3_service.delete_image(old_image_url)
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete old image: {cleanup_error}")
        
        logger.info(f"Admin {current_admin.username} updated event {event_id} with slug {db_event.slug}")
        return db_event
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        if new_image_url:
            try:
                s3_service.delete_image(new_image_url)
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
    db_event = db.query(Event).filter(Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")

    image_url = db_event.image_url
    
    try:
        db.delete(db_event)
        db.commit()
        
        if image_url:
            try:
                s3_service.delete_image(image_url)
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete image from S3: {cleanup_error}")
        
        logger.info(f"Admin {current_admin.username} deleted event {event_id}")
        return {"detail": "Event deleted"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting event: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting event: {str(e)}")