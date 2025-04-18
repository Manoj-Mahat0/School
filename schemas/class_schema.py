# schemas/class_schema.py
from pydantic import BaseModel

class ClassSectionCreate(BaseModel):
    class_name: str
    section: str
