from sqlalchemy import Column, Integer, String, Boolean, ForeignKey,Float ,Enum
from sqlalchemy.orm import relationship
from database import Base
import enum

class SchoolType(str, enum.Enum):
    highschool = "highschool"
    university = "university"

class Student(Base):
    __tablename__="students"
    id = Column(Integer,primary_key=True,index=True)
    name = Column(String,nullable=False)
    age = Column(Integer)
    grade = Column(String)
    photo_url = Column(String, default="")
    
    enrollments = relationship("Enrollment", back_populates="student")

    achievements = relationship(
        "Achievement",
        back_populates="student",
        cascade="all, delete-orphan"
    )



class School(Base):
    __tablename__="schools"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    type = Column(Enum(SchoolType), nullable=False)
    state = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    website = Column(String)
    state = Column(String)
    enrollments = relationship("Enrollment", back_populates="school")

class Enrollment(Base):
    __tablename__ = "enrollments"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    school_id = Column(Integer, ForeignKey("schools.id"))
    status = Column(String)  # "current" or "past"
    start_year = Column(Integer)
    end_year = Column(Integer)

    student = relationship("Student", back_populates="enrollments")
    school = relationship("School", back_populates="enrollments")


class Achievement(Base):
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey("students.id"), nullable=False)

    title = Column(String, nullable=False)

    student = relationship("Student", back_populates="achievements")