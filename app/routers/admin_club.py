# app/routers/admin_clubs.py (or wherever you place the router)
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.club import Club 
from app.schemas.club import ClubCreate, Club as ClubSchema
from app.auth.auth import get_current_admin
from app.services.s3_service import s3_service
from typing import List, Optional
import logging
import re
from PIL import Image
import io

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin/clubs", tags=["admin_clubs"])
public_club_router = APIRouter(prefix="/clubs", tags=["public_clubs"])

def generate_slug(name: str, db: Session, club_id: int = None) -> str:
    """Generate a unique slug from the name."""
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')
    base_slug = slug
    counter = 1
    while True:
        query = db.query(Club).filter(Club.slug == slug)
        if club_id:
            query = query.filter(Club.id != club_id)
        
        if not query.first():
            return slug
        
        slug = f"{base_slug}-{counter}"
        counter += 1

def optimize_and_upload_logo(image: UploadFile) -> str:
    """Optimize logo and upload to S3 (400x400 square for club logos)"""
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
        
        # Calculate dimensions to maintain aspect ratio and crop to 400x400
        target_size = 400
        img_ratio = img.width / img.height
        
        if img_ratio > 1:
            # Image is wider, scale by height
            new_height = target_size
            new_width = int(new_height * img_ratio)
        else:
            # Image is taller or square, scale by width
            new_width = target_size
            new_height = int(new_width / img_ratio)
        
        # Resize image
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Crop to exact dimensions (center crop)
        left = (new_width - target_size) // 2
        top = (new_height - target_size) // 2
        right = left + target_size
        bottom = top + target_size
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
        logo_url = s3_service.upload_image(optimized_file)
        
        return logo_url
        
    except Exception as e:
        logger.error(f"Error optimizing logo: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process logo: {str(e)}")

@public_club_router.get("/", response_model=List[ClubSchema])
def read_public_clubs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """Get all clubs with pagination (Public access)"""
    logger.debug(f"Accessing public clubs: skip={skip}, limit={limit}")
    try:
        clubs = db.query(Club).order_by(Club.name.asc()).offset(skip).limit(limit).all()
        logger.info(f"Retrieved {len(clubs)} clubs")
        return clubs
    except Exception as e:
        logger.error(f"Error fetching public clubs: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@public_club_router.get("/slug/{slug}", response_model=ClubSchema)
def read_public_club_by_slug(
    slug: str,
    db: Session = Depends(get_db)
):
    """Get a specific club by slug (Public access)"""
    logger.debug(f"Fetching public club by slug: {slug}")
    try:
        db_club = db.query(Club).filter(Club.slug == slug).first()
        if db_club is None:
            logger.warning(f"Club with slug {slug} not found")
            raise HTTPException(status_code=404, detail="Club not found")
        logger.info(f"Retrieved club with slug: {slug}")
        return db_club
    except Exception as e:
        logger.error(f"Error fetching club by slug {slug}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@public_club_router.get("/{club_id}", response_model=ClubSchema)
def read_public_club(
    club_id: int,
    db: Session = Depends(get_db)
):
    """Get a specific club by ID (Public access)"""
    logger.debug(f"Fetching public club ID: {club_id}")
    try:
        db_club = db.query(Club).filter(Club.id == club_id).first()
        if db_club is None:
            logger.warning(f"Club ID {club_id} not found")
            raise HTTPException(status_code=404, detail="Club not found")
        logger.info(f"Retrieved club ID: {club_id}")
        return db_club
    except Exception as e:
        logger.error(f"Error fetching club ID {club_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.post("/", response_model=ClubSchema)
async def create_club(
    name: str = Form(..., min_length=1, max_length=200),
    description: str = Form(..., min_length=1),
    logo: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Create a new club with optimized logo (Admin only)"""
    logger.debug(f"Creating club by admin: {current_admin.username}")
    
    logo_url = None
    try:
        # Validate logo if provided
        if logo:
            if not logo.content_type.startswith('image/'):
                logger.error(f"Invalid file type: {logo.content_type}")
                raise HTTPException(status_code=400, detail="File must be an image")
            if logo.size > 5 * 1024 * 1024:
                logger.error(f"Logo too large: {logo.size} bytes")
                raise HTTPException(status_code=400, detail="Logo must be less than 5MB")
            
            # Optimize and upload logo
            logger.debug(f"Optimizing and uploading logo: {logo.filename}")
            logo_url = optimize_and_upload_logo(logo)
            if not logo_url:
                logger.error("Failed to upload optimized logo")
                raise HTTPException(status_code=500, detail="Failed to upload logo")
            logger.debug(f"Logo uploaded successfully: {logo_url}")

        # Generate unique slug
        slug = generate_slug(name, db)
        logger.debug(f"Generated slug: {slug}")

        # Create club
        db_club = Club(
            name=name.strip(),
            description=description.strip(),
            logo_url=logo_url,
            slug=slug
        )
        db.add(db_club)
        db.commit()
        db.refresh(db_club)
        
        logger.info(f"Admin {current_admin.username} created club ID {db_club.id}: {name} (slug: {slug})")
        return db_club
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        if logo_url:
            try:
                s3_service.delete_image(logo_url)
                logger.debug(f"Cleaned up uploaded logo: {logo_url}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup uploaded logo: {cleanup_error}")
        
        logger.error(f"Error creating club: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error creating club: {str(e)}")

@router.get("/{club_id}", response_model=ClubSchema)
def read_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get a specific club by ID (Admin only)"""
    logger.debug(f"Admin {current_admin.username} fetching club ID: {club_id}")
    db_club = db.query(Club).filter(Club.id == club_id).first()
    if db_club is None:
        logger.warning(f"Club ID {club_id} not found")
        raise HTTPException(status_code=404, detail="Club not found")
    return db_club

@router.get("/", response_model=List[ClubSchema])
def read_clubs(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Get all clubs with pagination (Admin only)"""
    logger.debug(f"Admin {current_admin.username} fetching clubs: skip={skip}, limit={limit}")
    clubs = db.query(Club).order_by(Club.name.asc()).offset(skip).limit(limit).all()
    logger.info(f"Retrieved {len(clubs)} clubs for admin")
    return clubs

@router.put("/{club_id}", response_model=ClubSchema)
async def update_club(
    club_id: int,
    name: Optional[str] = Form(None),
    description: Optional[str] = Form(None),
    logo: Optional[UploadFile] = File(None),
    remove_logo: Optional[str] = Form("false"),
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Update an existing club with enhanced logo handling (Admin only)"""
    logger.debug(f"Updating club ID: {club_id} by admin: {current_admin.username}")
    logger.debug(f"Received parameters:")
    logger.debug(f"  - name: {name}")
    logger.debug(f"  - description: {description[:50] + '...' if description and len(description) > 50 else description}")
    logger.debug(f"  - logo: {logo.filename if logo else None}")
    logger.debug(f"  - remove_logo: {remove_logo}")
    
    # Fetch the existing club
    db_club = db.query(Club).filter(Club.id == club_id).first()
    if db_club is None:
        logger.warning(f"Club ID {club_id} not found")
        raise HTTPException(status_code=404, detail="Club not found")

    # Log current club state
    logger.debug(f"Current club state:")
    logger.debug(f"  - name: {db_club.name}")
    logger.debug(f"  - slug: {db_club.slug}")
    logger.debug(f"  - description: {db_club.description[:50] + '...' if len(db_club.description) > 50 else db_club.description}")
    logger.debug(f"  - logo_url: {db_club.logo_url}")

    new_logo_url = None
    old_logo_url = db_club.logo_url
    updated = False
    changes_made = []
    
    try:
        # Validate new logo if provided
        if logo:
            if not logo.content_type.startswith('image/'):
                logger.error(f"Invalid file type: {logo.content_type}")
                raise HTTPException(status_code=400, detail="File must be an image")
            if logo.size > 5 * 1024 * 1024:
                logger.error(f"Logo too large: {logo.size} bytes")
                raise HTTPException(status_code=400, detail="Logo must be less than 5MB")
        
        # Update name and regenerate slug if changed
        if name is not None:
            name_trimmed = name.strip()
            if name_trimmed != db_club.name:
                if len(name_trimmed) < 1 or len(name_trimmed) > 200:
                    logger.error(f"Invalid name length: {len(name_trimmed)}")
                    raise HTTPException(status_code=400, detail="Name must be 1-200 characters")
                
                logger.debug(f"Name change detected: '{db_club.name}' -> '{name_trimmed}'")
                db_club.name = name_trimmed
                
                # Regenerate slug when name changes
                new_slug = generate_slug(name_trimmed, db, club_id)
                logger.debug(f"Slug updated: '{db_club.slug}' -> '{new_slug}'")
                db_club.slug = new_slug
                
                updated = True
                changes_made.append("name")
                changes_made.append("slug")
            else:
                logger.debug("Name unchanged")

        # Update description
        if description is not None:
            description_trimmed = description.strip()
            if description_trimmed != db_club.description:
                if len(description_trimmed) < 1:
                    logger.error("Description cannot be empty")
                    raise HTTPException(status_code=400, detail="Description must not be empty")
                
                logger.debug(f"Description change detected (length: {len(db_club.description)} -> {len(description_trimmed)})")
                db_club.description = description_trimmed
                updated = True
                changes_made.append("description")
            else:
                logger.debug("Description unchanged")

        # Handle logo update or removal
        if logo:
            # Optimize and upload new logo
            logger.debug(f"Optimizing and uploading new logo: {logo.filename}")
            new_logo_url = optimize_and_upload_logo(logo)
            if not new_logo_url:
                logger.error("Failed to upload optimized logo")
                raise HTTPException(status_code=500, detail="Failed to upload logo")
            
            logger.debug(f"Logo change detected: '{db_club.logo_url}' -> '{new_logo_url}'")
            db_club.logo_url = new_logo_url
            updated = True
            changes_made.append("logo")
            
        elif remove_logo == "true" and db_club.logo_url:
            logger.debug(f"Removing existing logo: {db_club.logo_url}")
            db_club.logo_url = None
            updated = True
            changes_made.append("removed_logo")

        # Log update summary
        logger.debug(f"Update summary:")
        logger.debug(f"  - Changes detected: {updated}")
        logger.debug(f"  - Fields changed: {changes_made}")

        # Handle the case when no changes are detected
        if not updated:
            logger.info("No changes detected - returning existing club without error")
            return db_club

        # Commit changes
        db.commit()
        db.refresh(db_club)
        
        # Delete old logo if new one was uploaded successfully
        if new_logo_url and old_logo_url:
            try:
                s3_service.delete_image(old_logo_url)
                logger.debug(f"Deleted old logo: {old_logo_url}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete old logo: {cleanup_error}")
        
        # Delete old logo if removal was requested
        if remove_logo == "true" and old_logo_url:
            try:
                s3_service.delete_image(old_logo_url)
                logger.debug(f"Deleted removed logo: {old_logo_url}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete removed logo: {cleanup_error}")
        
        logger.info(f"Admin {current_admin.username} updated club ID {club_id}. Changes: {', '.join(changes_made)}")
        return db_club
        
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        if new_logo_url:
            try:
                s3_service.delete_image(new_logo_url)
                logger.debug(f"Cleaned up uploaded logo after error: {new_logo_url}")
            except Exception as cleanup_error:
                logger.error(f"Failed to cleanup uploaded logo: {cleanup_error}")
        
        logger.error(f"Error updating club: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error updating club: {str(e)}")

@router.delete("/{club_id}")
def delete_club(
    club_id: int,
    db: Session = Depends(get_db),
    current_admin=Depends(get_current_admin)
):
    """Delete a club (Admin only)"""
    logger.debug(f"Deleting club ID: {club_id} by admin: {current_admin.username}")
    db_club = db.query(Club).filter(Club.id == club_id).first()
    if db_club is None:
        logger.warning(f"Club ID {club_id} not found")
        raise HTTPException(status_code=404, detail="Club not found")

    logo_url = db_club.logo_url
    
    try:
        db.delete(db_club)
        db.commit()
        
        if logo_url:
            try:
                s3_service.delete_image(logo_url)
                logger.debug(f"Deleted logo: {logo_url}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to delete logo from S3: {cleanup_error}")
        
        logger.info(f"Admin {current_admin.username} deleted club ID {club_id}")
        return {"detail": "Club deleted"}
        
    except Exception as e:
        db.rollback()
        logger.error(f"Error deleting club: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting club: {str(e)}")