from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, List
from datetime import datetime
from app.models.leadership import CampusType, LeadershipCategory

class LeadershipBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    bio: Optional[str] = None
    year_of_service: str = Field(..., min_length=4, max_length=20)
    campus: CampusType
    category: LeadershipCategory
    position_title: str = Field(..., min_length=2, max_length=100)
    school_name: Optional[str] = Field(None, max_length=255)
    hall_name: Optional[str] = Field(None, max_length=255)
    display_order: Optional[int] = Field(0, ge=0)
    
    @field_validator('year_of_service')
    @classmethod
    def validate_year_format(cls, v):
        # Validate year format like "2024-2025" or "2024"
        if not v.replace('-', '').replace(' ', '').isdigit():
            if '-' not in v or len(v.split('-')) != 2:
                raise ValueError('Year of service must be in format "YYYY" or "YYYY-YYYY"')
            start_year, end_year = v.split('-')
            if not (start_year.isdigit() and end_year.isdigit()):
                raise ValueError('Year of service must contain valid years')
        return v

class LeadershipCreate(LeadershipBase):
    """Override validation for create - require school/hall names for specific categories"""
    
    @field_validator('school_name')
    @classmethod
    def validate_school_name_create(cls, v, info):
        if 'category' in info.data and info.data['category'] == LeadershipCategory.SCHOOL_REP and not v:
            raise ValueError('School name is required for school representatives')
        return v
    
    @field_validator('hall_name')
    @classmethod
    def validate_hall_name_create(cls, v, info):
        if 'category' in info.data and info.data['category'] in [
            LeadershipCategory.HALL_REP,
            LeadershipCategory.KAREN_HALL_REP
        ] and not v:
            raise ValueError('Hall name is required for hall representatives')
        return v

class LeadershipUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    bio: Optional[str] = None
    year_of_service: Optional[str] = Field(None, min_length=4, max_length=20)
    campus: Optional[CampusType] = None
    category: Optional[LeadershipCategory] = None
    position_title: Optional[str] = Field(None, min_length=2, max_length=100)
    school_name: Optional[str] = Field(None, max_length=255)
    hall_name: Optional[str] = Field(None, max_length=255)
    display_order: Optional[int] = Field(None, ge=0)
    
    @field_validator('year_of_service')
    @classmethod
    def validate_year_format(cls, v):
        if v is not None:
            if not v.replace('-', '').replace(' ', '').isdigit():
                if '-' not in v or len(v.split('-')) != 2:
                    raise ValueError('Year of service must be in format "YYYY" or "YYYY-YYYY"')
                start_year, end_year = v.split('-')
                if not (start_year.isdigit() and end_year.isdigit()):
                    raise ValueError('Year of service must contain valid years')
        return v

class Leadership(BaseModel):
    """Response model - NO validation requirements for school/hall names"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    year_of_service: str
    campus: CampusType
    category: LeadershipCategory
    position_title: str
    school_name: Optional[str] = None
    hall_name: Optional[str] = None
    display_order: int
    created_at: datetime
    updated_at: datetime

class LeadershipReorderRequest(BaseModel):
    leadership_items: List[dict] = Field(..., description="List of leadership items with id and new display_order")
    
    @field_validator('leadership_items')
    @classmethod
    def validate_leadership_items(cls, v):
        if not v:
            raise ValueError('Leadership items list cannot be empty')
        
        for item in v:
            if 'id' not in item or 'display_order' not in item:
                raise ValueError('Each item must have id and display_order')
            if not isinstance(item['id'], int) or not isinstance(item['display_order'], int):
                raise ValueError('id and display_order must be integers')
        
        return v

# Response models for different organizational views
class CampusLeadershipResponse(BaseModel):
    """Response for campus-specific leadership view"""
    campus: CampusType
    categories: dict  # Will contain categories with their leaders

class OrganizationalStructureResponse(BaseModel):
    """Response for complete organizational structure"""
    main_campus: dict
    karen_campus: dict
    cbd_campus: dict
    nakuru_campus: dict
    mombasa_campus: dict

class LeadershipSummary(BaseModel):
    """Summary view of leadership"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    name: str
    position_title: str
    campus: CampusType
    category: LeadershipCategory
    year_of_service: str
    profile_image_url: Optional[str] = None
    display_order: int