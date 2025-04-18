from pydantic import BaseModel

class StudentFeeStatus(BaseModel):
    student_id: int
    class_section_id: int
    paid_amount: float
    status: str  # "Pending" or "Paid"

class FeePaymentUpdate(BaseModel):
    paid_amount: float
    status: str  # "Pending" or "Paid"
