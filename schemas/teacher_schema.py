from pydantic import BaseModel

class TeacherCreate(BaseModel):
    name: str
    email: str
    password: str
    class_section_id: int  # ✅ Link teacher to a class-section