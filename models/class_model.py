# models/class_model.py
from sqlalchemy import Column, Integer, String
from db.database import Base

class ClassSection(Base):
    __tablename__ = "class_sections"

    id = Column(Integer, primary_key=True, index=True)
    class_name = Column(String(100))
    section = Column(String(10))
