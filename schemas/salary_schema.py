from pydantic import BaseModel

class SetSalary(BaseModel):
    teacher_id: int
    salary_amount: float
