from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class College(Base):
    __tablename__ = "colleges"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)

class School(Base):
    __tablename__ = "schools"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)

class student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False, index=True)
    phone_number = Column(String, nullable=True)
    registration_number = Column(String, unique=True, nullable=False, index=True)
    college_id = Column(Integer, ForeignKey("colleges.id"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id"), nullable=False)
    course = Column(String, nullable=False)
    year_of_study = Column(Integer, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    verification_token = Column(String, nullable=True)