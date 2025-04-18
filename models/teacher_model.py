from sqlalchemy import Column, Integer, String, ForeignKey
from db.database import Base

class Teacher(Base):
    __tablename__ = "teachers"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))
    email = Column(String(100), unique=True)
    password = Column(String(255))
    class_section_id = Column(Integer, ForeignKey("class_sections.id"))  # ✅ New
    created_by = Column(Integer, ForeignKey("users.id"))
