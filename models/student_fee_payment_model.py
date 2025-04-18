from sqlalchemy import Column, Integer, Float, String, ForeignKey, DateTime
from db.database import Base
from datetime import datetime

class StudentFeePayment(Base):
    __tablename__ = "student_fee_payment"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id"))
    class_section_id = Column(Integer, ForeignKey("class_sections.id"))
    paid_amount = Column(Float, default=0)
    status = Column(String(20), default="Pending")  # Pending or Paid
    payment_date = Column(DateTime, default=datetime.utcnow)
