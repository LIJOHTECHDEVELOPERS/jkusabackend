from sqlalchemy import Column, Integer, String, DateTime, Enum as SQLEnum
from sqlalchemy.sql import func
from app.database import Base
import enum

class IDType(str, enum.Enum):
    SCHOOL_ID = "School ID"
    NATIONAL_ID = "National ID"
    PASSPORT = "Passport"
    OTHER = "Other"

class IDStatus(str, enum.Enum):
    AVAILABLE = "Available"
    COLLECTED = "Collected"

class Station(str, enum.Enum):
    ADMIN_BLOCK = "Administration Block A Reception"
    LIBRARY = "Library Reception"
    GATE_A = "Main Gate A"
    GATE_B = "Gate B Security" 
    GATE_C = "Gate C Security"
    GATE_D = "Gate D Security"
    GATE_E = "Gate E Security"
    TECH_HOUSE = "Tech House Security"
    HALL_1 = "Hall 1 Security"
    HALL_2 = "Hall 2 Security"
    HALL_3 = "Hall 3 Security" 
    HALL_4 = "Hall 4 Security"
    HALL_5 = "Hall 5 Security"
    HALL_6 = "Hall 6 Security"
    NSC_BUILDING = "NSC Building Security"

class LostID(Base):
    __tablename__ = "lost_ids"

    id = Column(Integer, primary_key=True, index=True)
    name_on_id = Column(String, nullable=False, index=True)
    id_type = Column(SQLEnum(IDType), nullable=False)
    id_number = Column(String, nullable=True, index=True)
    station = Column(SQLEnum(Station), nullable=False)
    description = Column(String, nullable=True)
    posted_by = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    status = Column(SQLEnum(IDStatus), default=IDStatus.AVAILABLE, nullable=False)
    collected_by = Column(String, nullable=True)
    collected_phone = Column(String, nullable=True)
    date_posted = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    date_collected = Column(DateTime(timezone=True), nullable=True)