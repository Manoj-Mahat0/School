# models/teacher_class_map_model.py
from sqlalchemy import Column, Integer, ForeignKey
from db.database import Base

class TeacherClassMap(Base):
    __tablename__ = "teacher_class_map"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    class_section_id = Column(Integer, ForeignKey("class_sections.id"))
