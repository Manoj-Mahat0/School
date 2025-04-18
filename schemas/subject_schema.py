# schemas/subject_schema.py
from pydantic import BaseModel

class SubjectCreate(BaseModel):
    subject_name: str
    class_section_id: int
