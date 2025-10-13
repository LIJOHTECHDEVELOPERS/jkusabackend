"""
Lost & Found ID System Router
Complete API endpoints for managing lost and found IDs
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_, func, and_
from typing import List, Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.models.lost_id import LostID, IDStatus, Station, IDType
from app.schemas.lost_id import (
    PostIDRequest, 
    MarkCollectedRequest, 
    LostIDResponse,
    LostIDListResponse,
    SystemInfoResponse,
    StationInfo,
    IDTypeInfo,
    DeleteResponse,
    StationStatistics,
    DetailedStatisticsResponse,
    IDFilterParams
)

import logging

logger = logging.getLogger(__name__)

# ==================== ROUTER SETUP ====================

router = APIRouter(
    prefix="/api/lost-ids",
    tags=["Lost & Found IDs"]
)


# ==================== HELPER FUNCTIONS ====================

def get_id_or_404(db: Session, id_record: int) -> LostID:
    """
    Get a Lost ID record by ID or raise 404 error.
    
    Args:
        db: Database session
        id_record: ID of the record to fetch
        
    Returns:
        LostID object
        
    Raises:
        HTTPException: 404 if record not found
    """
    lost_id = db.query(LostID).filter(LostID.id == id_record).first()
    if not lost_id:
        logger.warning(f"ID record {id_record} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"ID record with id {id_record} not found"
        )
    return lost_id


def build_filter_query(db: Session, filters: IDFilterParams = None):
    """
    Build a filtered query based on provided parameters.
    
    Args:
        db: Database session
        filters: Filter parameters
        
    Returns:
        SQLAlchemy query object
    """
    query = db.query(LostID)
    
    if not filters:
        return query
    
    if filters.status:
        query = query.filter(LostID.status == filters.status)
    
    if filters.station:
        query = query.filter(LostID.station == filters.station)
    
    if filters.id_type:
        query = query.filter(LostID.id_type == filters.id_type)
    
    if filters.date_from:
        query = query.filter(LostID.date_posted >= filters.date_from)
    
    if filters.date_to:
        query = query.filter(LostID.date_posted <= filters.date_to)
    
    return query


# ==================== MAIN ENDPOINTS ====================

@router.post(
    "",
    response_model=LostIDResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Post a Found ID",
    description="Submit details about a found ID to the system. Anyone can post."
)
async def post_found_id(
    request: PostIDRequest,
    db: Session = Depends(get_db)
):
    """
    Post a found ID to the system.
    
    This endpoint allows anyone who finds an ID to report it by providing:
    - Name on the ID
    - ID type (School ID, National ID, etc.)
    - Station where it will be dropped off
    - Optional: ID number, description, finder's contact info
    
    The ID will be marked as "Available" and appear in public listings.
    """
    try:
        logger.info(f"Creating new ID record for: {request.name_on_id}")
        
        new_id = LostID(
            name_on_id=request.name_on_id.strip(),
            id_type=request.id_type,
            id_number=request.id_number.strip() if request.id_number else None,
            station=request.station,
            description=request.description.strip() if request.description else None,
            posted_by=request.posted_by.strip() if request.posted_by else None,
            phone=request.phone.strip() if request.phone else None,
            status=IDStatus.AVAILABLE
        )
        
        db.add(new_id)
        db.commit()
        db.refresh(new_id)
        
        logger.info(f"Successfully created ID record {new_id.id}")
        return new_id
        
    except Exception as e:
        logger.error(f"Error creating ID record: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create ID record. Please try again."
        )


@router.get(
    "",
    response_model=List[LostIDResponse],
    summary="Get All Lost IDs",
    description="Retrieve all posted IDs with optional filtering and pagination."
)
async def get_all_ids(
    status_filter: Optional[IDStatus] = Query(None, alias="status", description="Filter by status"),
    station: Optional[Station] = Query(None, description="Filter by station"),
    id_type: Optional[IDType] = Query(None, description="Filter by ID type"),
    limit: int = Query(100, ge=1, le=500, description="Number of results to return"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    db: Session = Depends(get_db)
):
    """
    Get all posted IDs with optional filtering.
    
    Results are sorted by most recent first (newest on top).
    
    Query Parameters:
    - status: Filter by Available or Collected
    - station: Filter by specific station
    - id_type: Filter by ID type
    - limit: Maximum number of results (1-500, default: 100)
    - offset: Number of results to skip for pagination
    """
    try:
        query = db.query(LostID)
        
        # Apply filters
        if status_filter:
            query = query.filter(LostID.status == status_filter)
        
        if station:
            query = query.filter(LostID.station == station)
        
        if id_type:
            query = query.filter(LostID.id_type == id_type)
        
        # Sort by newest first
        query = query.order_by(LostID.date_posted.desc())
        
        # Apply pagination
        ids = query.offset(offset).limit(limit).all()
        
        logger.info(f"Retrieved {len(ids)} ID records")
        return ids
        
    except Exception as e:
        logger.error(f"Error retrieving IDs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve ID records"
        )


@router.get(
    "/search",
    response_model=List[LostIDResponse],
    summary="Search for Lost IDs",
    description="Search for IDs by name or ID number with case-insensitive partial matching."
)
async def search_ids(
    q: str = Query(..., min_length=2, description="Search by name or ID number"),
    status_filter: Optional[IDStatus] = Query(None, alias="status", description="Filter by status"),
    station: Optional[Station] = Query(None, description="Filter by station"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results"),
    db: Session = Depends(get_db)
):
    """
    Search for IDs by name or ID number.
    
    The search is case-insensitive and matches partial strings.
    For example, searching "john" will find "John Doe", "Johnny", etc.
    
    Query Parameters:
    - q: Search term (minimum 2 characters)
    - status: Optional status filter
    - station: Optional station filter
    - limit: Maximum number of results
    """
    try:
        search_term = f"%{q.strip()}%"
        
        logger.info(f"Searching for IDs with term: {q}")
        
        # Search in both name and ID number fields
        query = db.query(LostID).filter(
            or_(
                LostID.name_on_id.ilike(search_term),
                LostID.id_number.ilike(search_term)
            )
        )
        
        # Apply additional filters
        if status_filter:
            query = query.filter(LostID.status == status_filter)
        
        if station:
            query = query.filter(LostID.station == station)
        
        # Sort by most recent
        query = query.order_by(LostID.date_posted.desc())
        
        results = query.limit(limit).all()
        
        logger.info(f"Found {len(results)} matching records")
        return results
        
    except Exception as e:
        logger.error(f"Error searching IDs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Search failed. Please try again."
        )


@router.get(
    "/{id_record}",
    response_model=LostIDResponse,
    summary="Get Single ID Record",
    description="Retrieve detailed information about a specific ID record."
)
async def get_id_by_record(
    id_record: int,
    db: Session = Depends(get_db)
):
    """
    Get a specific ID record by its database ID.
    
    Parameters:
    - id_record: The unique ID of the record
    
    Returns:
    - Complete ID record with all details
    """
    logger.info(f"Fetching ID record {id_record}")
    return get_id_or_404(db, id_record)


@router.put(
    "/{id_record}/collect",
    response_model=LostIDResponse,
    summary="Mark ID as Collected",
    description="Mark an ID as collected after the owner retrieves it from the station."
)
async def mark_id_collected(
    id_record: int,
    request: MarkCollectedRequest,
    db: Session = Depends(get_db)
):
    """
    Mark an ID as collected by the rightful owner.
    
    This should be done AFTER the owner has physically retrieved 
    the ID from the mentioned station.
    
    The system records:
    - Who collected it (name)
    - Contact phone number
    - Timestamp of collection
    
    Once marked as collected, the ID cannot be collected again.
    """
    try:
        logger.info(f"Attempting to mark ID {id_record} as collected")
        
        lost_id = get_id_or_404(db, id_record)
        
        # Check if already collected
        if lost_id.status == IDStatus.COLLECTED:
            logger.warning(f"ID {id_record} already collected")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"This ID has already been marked as collected on {lost_id.date_collected}"
            )
        
        # Update the record
        lost_id.status = IDStatus.COLLECTED
        lost_id.collected_by = request.collected_by.strip()
        lost_id.collected_phone = request.collected_phone.strip()
        lost_id.date_collected = datetime.utcnow()
        
        db.commit()
        db.refresh(lost_id)
        
        logger.info(f"Successfully marked ID {id_record} as collected by {lost_id.collected_by}")
        return lost_id
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking ID as collected: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark ID as collected"
        )


@router.get(
    "/stats/info",
    response_model=SystemInfoResponse,
    summary="Get System Information",
    description="Get system configuration and basic statistics."
)
async def get_system_info(db: Session = Depends(get_db)):
    """
    Get system information including:
    - Available stations (dropdown options)
    - Available ID types (dropdown options)
    - Total number of IDs in system
    - Number of available IDs
    - Number of collected IDs
    
    This is useful for populating dropdowns and showing statistics.
    """
    try:
        logger.info("Fetching system information")
        
        # Get counts
        total = db.query(func.count(LostID.id)).scalar()
        available = db.query(func.count(LostID.id)).filter(
            LostID.status == IDStatus.AVAILABLE
        ).scalar()
        collected = db.query(func.count(LostID.id)).filter(
            LostID.status == IDStatus.COLLECTED
        ).scalar()
        
        # Get all stations
        stations = [
            StationInfo(value=station.value, label=station.value)
            for station in Station
        ]
        
        # Get all ID types
        id_types = [
            IDTypeInfo(value=id_type.value, label=id_type.value)
            for id_type in IDType
        ]
        
        return SystemInfoResponse(
            stations=stations,
            id_types=id_types,
            total_ids=total or 0,
            available_ids=available or 0,
            collected_ids=collected or 0
        )
        
    except Exception as e:
        logger.error(f"Error fetching system info: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system information"
        )


@router.get(
    "/stats/detailed",
    response_model=DetailedStatisticsResponse,
    summary="Get Detailed Statistics",
    description="Get comprehensive statistics including per-station breakdown and recent activity."
)
async def get_detailed_statistics(db: Session = Depends(get_db)):
    """
    Get detailed statistics including:
    - Overall system stats
    - Per-station breakdown
    - Recent activity (last 7 days)
    """
    try:
        logger.info("Fetching detailed statistics")
        
        # Get overall stats
        total = db.query(func.count(LostID.id)).scalar() or 0
        available = db.query(func.count(LostID.id)).filter(
            LostID.status == IDStatus.AVAILABLE
        ).scalar() or 0
        collected = db.query(func.count(LostID.id)).filter(
            LostID.status == IDStatus.COLLECTED
        ).scalar() or 0
        
        # Get per-station statistics
        station_stats = []
        for station in Station:
            station_total = db.query(func.count(LostID.id)).filter(
                LostID.station == station
            ).scalar() or 0
            
            station_available = db.query(func.count(LostID.id)).filter(
                and_(LostID.station == station, LostID.status == IDStatus.AVAILABLE)
            ).scalar() or 0
            
            station_collected = db.query(func.count(LostID.id)).filter(
                and_(LostID.station == station, LostID.status == IDStatus.COLLECTED)
            ).scalar() or 0
            
            station_stats.append(
                StationStatistics(
                    station=station,
                    total_ids=station_total,
                    available_ids=station_available,
                    collected_ids=station_collected
                )
            )
        
        # Get recent activity (last 7 days)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        recent_posts = db.query(func.count(LostID.id)).filter(
            LostID.date_posted >= seven_days_ago
        ).scalar() or 0
        
        recent_collections = db.query(func.count(LostID.id)).filter(
            and_(
                LostID.date_collected >= seven_days_ago,
                LostID.status == IDStatus.COLLECTED
            )
        ).scalar() or 0
        
        # Build stations and id_types lists
        stations = [StationInfo(value=s.value, label=s.value) for s in Station]
        id_types = [IDTypeInfo(value=t.value, label=t.value) for t in IDType]
        
        overview = SystemInfoResponse(
            stations=stations,
            id_types=id_types,
            total_ids=total,
            available_ids=available,
            collected_ids=collected
        )
        
        return DetailedStatisticsResponse(
            overview=overview,
            by_station=station_stats,
            recent_posts=recent_posts,
            recent_collections=recent_collections
        )
        
    except Exception as e:
        logger.error(f"Error fetching detailed statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve detailed statistics"
        )


@router.delete(
    "/{id_record}",
    response_model=DeleteResponse,
    summary="Delete ID Record",
    description="Delete an ID record from the system (for cleanup or mistakes)."
)
async def delete_id_record(
    id_record: int,
    db: Session = Depends(get_db)
):
    """
    Delete an ID record from the system.
    
    This is useful for:
    - Removing duplicate entries
    - Cleaning up test data
    - Correcting mistakes
    
    NOTE: In production, you might want to add authentication
    to this endpoint to prevent unauthorized deletions.
    """
    try:
        logger.info(f"Attempting to delete ID record {id_record}")
        
        lost_id = get_id_or_404(db, id_record)
        
        db.delete(lost_id)
        db.commit()
        
        logger.info(f"Successfully deleted ID record {id_record}")
        
        return DeleteResponse(
            message="ID record deleted successfully",
            id=id_record
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting ID record: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete ID record"
        )


# ==================== UTILITY ENDPOINTS ====================

@router.get(
    "/by-station/{station}",
    response_model=List[LostIDResponse],
    summary="Get IDs by Station",
    description="Get all IDs at a specific station."
)
async def get_ids_by_station(
    station: Station,
    status_filter: Optional[IDStatus] = Query(None, alias="status"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db)
):
    """
    Get all IDs at a specific station.
    Useful for station staff to see what IDs they're holding.
    """
    try:
        query = db.query(LostID).filter(LostID.station == station)
        
        if status_filter:
            query = query.filter(LostID.status == status_filter)
        
        query = query.order_by(LostID.date_posted.desc())
        
        results = query.limit(limit).all()
        
        logger.info(f"Retrieved {len(results)} IDs for station {station.value}")
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving IDs by station: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve IDs for station"
        )


@router.get(
    "/recent/available",
    response_model=List[LostIDResponse],
    summary="Get Recent Available IDs",
    description="Get the most recently posted available IDs."
)
async def get_recent_available_ids(
    days: int = Query(7, ge=1, le=90, description="Number of days to look back"),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get recently posted IDs that are still available.
    Default: Last 7 days, maximum 20 results.
    """
    try:
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        results = db.query(LostID).filter(
            and_(
                LostID.status == IDStatus.AVAILABLE,
                LostID.date_posted >= cutoff_date
            )
        ).order_by(LostID.date_posted.desc()).limit(limit).all()
        
        logger.info(f"Retrieved {len(results)} recent available IDs")
        return results
        
    except Exception as e:
        logger.error(f"Error retrieving recent IDs: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve recent IDs"
        )


@router.patch(
    "/{id_record}",
    response_model=LostIDResponse,
    summary="Update ID Record",
    description="Update details of an ID record (before collection)."
)
async def update_id_record(
    id_record: int,
    name_on_id: Optional[str] = None,
    id_number: Optional[str] = None,
    description: Optional[str] = None,
    station: Optional[Station] = None,
    db: Session = Depends(get_db)
):
    """
    Update an existing ID record.
    Only provided fields will be updated.
    Cannot update records that have been collected.
    """
    try:
        logger.info(f"Updating ID record {id_record}")
        
        lost_id = get_id_or_404(db, id_record)
        
        if lost_id.status == IDStatus.COLLECTED:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot update a collected ID record"
            )
        
        # Update fields if provided
        if name_on_id:
            lost_id.name_on_id = name_on_id.strip()
        if id_number:
            lost_id.id_number = id_number.strip()
        if description:
            lost_id.description = description.strip()
        if station:
            lost_id.station = station
        
        db.commit()
        db.refresh(lost_id)
        
        logger.info(f"Successfully updated ID record {id_record}")
        return lost_id
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating ID record: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update ID record"
        )


# ==================== HEALTH CHECK ====================

@router.get(
    "/health/check",
    summary="Health Check",
    description="Check if the Lost & Found system is operational."
)
async def health_check(db: Session = Depends(get_db)):
    """
    Simple health check endpoint to verify system is running.
    """
    try:
        # Try a simple database query
        db.query(LostID).first()
        return {
            "status": "healthy",
            "service": "Lost & Found ID System",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is temporarily unavailable"
        )