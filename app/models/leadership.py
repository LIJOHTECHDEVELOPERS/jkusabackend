from sqlalchemy import Column, Integer, String, Text, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum

class CampusType(enum.Enum):
    MAIN = "MAIN"  # Changed to uppercase to match database
    KAREN = "KAREN"
    CBD = "CBD"
    NAKURU = "NAKURU"
    MOMBASA = "MOMBASA"

class LeadershipCategory(enum.Enum):
    # Main Campus
    MAIN_EXECUTIVE = "MAIN_EXECUTIVE"  # Changed to uppercase
    SCHOOL_REP = "SCHOOL_REP"
    HALL_REP = "HALL_REP"
    LEGAL_AFFAIRS_REP = "LEGAL_AFFAIRS_REP"
    SPECIAL_NEEDS_REP = "SPECIAL_NEEDS_REP"
    
    # Other Campuses
    KAREN_EXECUTIVE = "KAREN_EXECUTIVE"
    KAREN_LAW_REP = "KAREN_LAW_REP"
    KAREN_HALL_REP = "KAREN_HALL_REP"
    
    CBD_EXECUTIVE = "CBD_EXECUTIVE"
    NAKURU_EXECUTIVE = "NAKURU_EXECUTIVE"
    MOMBASA_EXECUTIVE = "MOMBASA_EXECUTIVE"

class MainExecutivePosition(enum.Enum):
    CHAIR = "CHAIR"
    VICE_CHAIR = "VICE_CHAIR"
    FINANCE_SECRETARY = "FINANCE_SECRETARY"
    ACADEMIC_SECRETARY = "ACADEMIC_SECRETARY"
    SECRETARY_GENERAL = "SECRETARY_GENERAL"
    SPORTS_ENTERTAINMENT_SECRETARY = "SPORTS_ENTERTAINMENT_SECRETARY"
    ACCOMMODATION_SECRETARY = "ACCOMMODATION_SECRETARY"
    SPEAKER = "SPEAKER"
    DEPUTY_SPEAKER = "DEPUTY_SPEAKER"

class OtherCampusPosition(enum.Enum):
    GOVERNOR = "GOVERNOR"
    DEPUTY_GOVERNOR = "DEPUTY_GOVERNOR"
    SECRETARY_GENERAL = "SECRETARY_GENERAL"
    TREASURER = "TREASURER"

class Leadership(Base):
    __tablename__ = "leadership"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    bio = Column(Text)
    profile_image_url = Column(String(500))
    year_of_service = Column(String(20), nullable=False)  # e.g., "2024-2025"
    
    # Campus and category - using uppercase values
    campus = Column(SQLEnum(CampusType), nullable=False)
    category = Column(SQLEnum(LeadershipCategory), nullable=False)
    
    # Position (flexible to handle different position types)
    position_title = Column(String(100), nullable=False)  # Custom title for flexibility
    
    # For specific school/hall representation
    school_name = Column(String(255))  # For school reps
    hall_name = Column(String(255))    # For hall reps
    
    # Display order for drag-and-drop functionality
    display_order = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<Leadership(name='{self.name}', position='{self.position_title}', campus='{self.campus}')>"