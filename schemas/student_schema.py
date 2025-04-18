from pydantic import BaseModel

class StudentCreate(BaseModel):
    name: str
    email: str
    password: str
    age: int
    gender: str
    class_name: str
    class_section_id: int  # ✅ Required
