from sqlalchemy import Column, Integer, ForeignKey
from db.database import Base

class SubjectTeacherMap(Base):
    __tablename__ = "subject_teacher_map"

    id = Column(Integer, primary_key=True, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id"))
    teacher_id = Column(Integer, ForeignKey("teachers.id"))
    class_section_id = Column(Integer, ForeignKey("class_sections.id"))
