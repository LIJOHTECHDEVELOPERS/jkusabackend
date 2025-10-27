# =============================================================================
# FILE: app/schemas/lost_id.py
# =============================================================================
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.lost_id import IDType, IDStatus, Station


# ==================== REQUEST SCHEMAS ====================

class PostIDRequest(BaseModel):
    """
    Schema for posting a found ID to the system.
    Used when someone finds an ID and wants to report it.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "name_on_id": "John Doe",
                "id_type": "School ID",
                "id_number": "SCT221-0001/2022",
                "station": "Library",
                "description": "Found near the computer lab on 2nd floor",
                "posted_by": "Jane Smith",
                "phone": "0712345678"
            }
        }
    )
    
    name_on_id: str = Field(
        ..., 
        min_length=2, 
        max_length=100, 
        description="Name written on the physical ID"
    )
    id_type: IDType = Field(
        ..., 
        description="Type of ID (School ID, National ID, Passport, Other)"
    )
    id_number: Optional[str] = Field(
        None, 
        max_length=50, 
        description="ID number if visible and readable"
    )
    station: Station = Field(
        ..., 
        description="Drop-off station where the ID will be kept"
    )
    description: Optional[str] = Field(
        None, 
        max_length=500, 
        description="Additional details about where/how the ID was found"
    )
    posted_by: Optional[str] = Field(
        None, 
        max_length=100, 
        description="Name of the person who found the ID (optional)"
    )
    phone: Optional[str] = Field(
        None, 
        max_length=20, 
        description="Phone number of the finder (optional)"
    )

    @field_validator('name_on_id', 'posted_by')
    @classmethod
    def validate_names(cls, v):
        if v:
            v = v.strip()
            if not v:
                raise ValueError('Name cannot be empty or just whitespace')
        return v

    @field_validator('phone')
    @classmethod
    def validate_phone(cls, v):
        if v:
            v = v.strip()
            # Remove common separators
            cleaned = v.replace(' ', '').replace('-', '').replace('+', '')
            if not cleaned.isdigit():
                raise ValueError('Phone number must contain only digits')
            if len(cleaned) < 9 or len(cleaned) > 15:
                raise ValueError('Phone number must be between 9 and 15 digits')
        return v


class MarkCollectedRequest(BaseModel):
    """
    Schema for marking an ID as collected.
    Used when the rightful owner retrieves their ID from the station.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "collected_by": "John Doe",
                "collected_phone": "0798765432"
            }
        }
    )
    
    collected_by: str = Field(
        ..., 
        min_length=2, 
        max_length=100, 
        description="Full name of the person collecting the ID"
    )
    collected_phone: str = Field(
        ..., 
        min_length=9, 
        max_length=20, 
        description="Phone number for verification and contact"
    )

    @field_validator('collected_by')
    @classmethod
    def validate_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError('Name cannot be empty')
        return v

    @field_validator('collected_phone')
    @classmethod
    def validate_phone(cls, v):
        v = v.strip()
        cleaned = v.replace(' ', '').replace('-', '').replace('+', '')
        if not cleaned.isdigit():
            raise ValueError('Phone number must contain only digits')
        if len(cleaned) < 9 or len(cleaned) > 15:
            raise ValueError('Phone number must be between 9 and 15 digits')
        return v


# ==================== RESPONSE SCHEMAS ====================

class LostIDResponse(BaseModel):
    """
    Schema for Lost ID response.
    Returns complete information about a lost/found ID record.
    """
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": 1,
                "name_on_id": "John Doe",
                "id_type": "School ID",
                "id_number": "SCT221-0001/2022",
                "station": "Library",
                "description": "Found near computer lab",
                "posted_by": "Jane Smith",
                "phone": "0712345678",
                "status": "Available",
                "collected_by": None,
                "collected_phone": None,
                "date_posted": "2025-10-13T10:30:00Z",
                "date_collected": None
            }
        }
    )
    
    id: int = Field(..., description="Unique database ID for this record")
    name_on_id: str = Field(..., description="Name written on the ID")
    id_type: IDType = Field(..., description="Type of identification")
    id_number: Optional[str] = Field(None, description="ID number if available")
    station: Station = Field(..., description="Station where ID is kept")
    description: Optional[str] = Field(None, description="Details about where found")
    posted_by: Optional[str] = Field(None, description="Name of finder")
    phone: Optional[str] = Field(None, description="Finder's phone number")
    status: IDStatus = Field(..., description="Current status (Available/Collected)")
    collected_by: Optional[str] = Field(None, description="Name of person who collected")
    collected_phone: Optional[str] = Field(None, description="Phone of person who collected")
    date_posted: datetime = Field(..., description="When the ID was posted to system")
    date_collected: Optional[datetime] = Field(None, description="When the ID was collected")


class LostIDListResponse(BaseModel):
    """
    Schema for paginated list of Lost IDs.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "id": 1,
                        "name_on_id": "John Doe",
                        "id_type": "School ID",
                        "station": "Library",
                        "status": "Available",
                        "date_posted": "2025-10-13T10:30:00Z"
                    }
                ],
                "total": 50,
                "limit": 20,
                "offset": 0
            }
        }
    )
    
    items: List[LostIDResponse]
    total: int = Field(..., description="Total number of records")
    limit: int = Field(..., description="Number of items per page")
    offset: int = Field(..., description="Current offset")


class StationInfo(BaseModel):
    """
    Schema for station information.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "value": "Library",
                "label": "Library"
            }
        }
    )
    
    value: str = Field(..., description="Station enum value")
    label: str = Field(..., description="Human-readable station name")


class IDTypeInfo(BaseModel):
    """
    Schema for ID type information.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "value": "School ID",
                "label": "School ID"
            }
        }
    )
    
    value: str = Field(..., description="ID type enum value")
    label: str = Field(..., description="Human-readable ID type name")


class SystemInfoResponse(BaseModel):
    """
    Schema for system information and statistics.
    Provides configuration data and current statistics.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "stations": [
                    {"value": "Security Office", "label": "Security Office"},
                    {"value": "Library", "label": "Library"}
                ],
                "id_types": [
                    {"value": "School ID", "label": "School ID"},
                    {"value": "National ID", "label": "National ID"}
                ],
                "total_ids": 50,
                "available_ids": 35,
                "collected_ids": 15
            }
        }
    )
    
    stations: List[StationInfo] = Field(..., description="Available drop-off stations")
    id_types: List[IDTypeInfo] = Field(..., description="Available ID types")
    total_ids: int = Field(..., description="Total number of IDs in system")
    available_ids: int = Field(..., description="Number of IDs currently available")
    collected_ids: int = Field(..., description="Number of IDs that have been collected")


class SearchQuery(BaseModel):
    """
    Schema for search query parameters.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "query": "John",
                "status": "Available"
            }
        }
    )
    
    query: str = Field(
        ..., 
        min_length=2, 
        max_length=100,
        description="Search term for name or ID number"
    )
    status: Optional[IDStatus] = Field(
        None,
        description="Filter by status"
    )


class DeleteResponse(BaseModel):
    """
    Schema for delete operation response.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "ID record deleted successfully",
                "id": 1
            }
        }
    )
    
    message: str = Field(..., description="Success message")
    id: int = Field(..., description="ID of deleted record")


class ErrorResponse(BaseModel):
    """
    Schema for error responses.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "detail": "ID record not found"
            }
        }
    )
    
    detail: str = Field(..., description="Error message")


class SuccessResponse(BaseModel):
    """
    Schema for generic success responses.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "message": "Operation completed successfully",
                "data": {"id": 1}
            }
        }
    )
    
    message: str = Field(..., description="Success message")
    data: Optional[dict] = Field(None, description="Additional data")


# ==================== FILTER SCHEMAS ====================

class IDFilterParams(BaseModel):
    """
    Schema for filtering Lost IDs.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "Available",
                "station": "Library",
                "id_type": "School ID"
            }
        }
    )
    
    status: Optional[IDStatus] = Field(None, description="Filter by status")
    station: Optional[Station] = Field(None, description="Filter by station")
    id_type: Optional[IDType] = Field(None, description="Filter by ID type")
    date_from: Optional[datetime] = Field(None, description="Filter from this date")
    date_to: Optional[datetime] = Field(None, description="Filter to this date")


# ==================== STATISTICS SCHEMAS ====================

class StationStatistics(BaseModel):
    """
    Schema for per-station statistics.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "station": "Library",
                "total_ids": 15,
                "available_ids": 10,
                "collected_ids": 5
            }
        }
    )
    
    station: Station
    total_ids: int
    available_ids: int
    collected_ids: int


class DetailedStatisticsResponse(BaseModel):
    """
    Schema for detailed system statistics.
    """
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "overview": {
                    "total_ids": 50,
                    "available_ids": 35,
                    "collected_ids": 15
                },
                "by_station": [
                    {
                        "station": "Library",
                        "total_ids": 15,
                        "available_ids": 10,
                        "collected_ids": 5
                    }
                ],
                "recent_posts": 8,
                "recent_collections": 3
            }
        }
    )
    
    overview: SystemInfoResponse
    by_station: List[StationStatistics]
    recent_posts: int = Field(..., description="IDs posted in last 7 days")
    recent_collections: int = Field(..., description="IDs collected in last 7 days")