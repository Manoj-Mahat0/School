# models/subject_model.py
from sqlalchemy import Column, Integer, String, ForeignKey
from db.database import Base

class Subject(Base):
    __tablename__ = "subjects"
    id = Column(Integer, primary_key=True, index=True)
    subject_name = Column(String(100))
    class_section_id = Column(Integer, ForeignKey("class_sections.id"))
    created_by = Column(Integer, ForeignKey("teachers.id"))
