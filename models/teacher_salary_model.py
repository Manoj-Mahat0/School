from sqlalchemy import Column, Integer, Float, ForeignKey
from db.database import Base

class TeacherSalary(Base):
    __tablename__ = "teacher_salary"

    id = Column(Integer, primary_key=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id"), unique=True)
    salary_amount = Column(Float)
