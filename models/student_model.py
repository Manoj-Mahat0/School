from sqlalchemy import Column, Integer, String, ForeignKey
from db.database import Base

class Student(Base):
    __tablename__ = "students"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    password = Column(String(255))
    age = Column(Integer)
    gender = Column(String(10))
    class_name = Column(String(100))
    created_by = Column(Integer, ForeignKey("teachers.id"))
    class_section_id = Column(Integer, ForeignKey("class_sections.id"))  # ✅ Add this line
