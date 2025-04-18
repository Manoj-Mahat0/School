from pydantic import BaseModel
from typing import List

class AssignTeacherClasses(BaseModel):
    teacher_id: int
    class_section_ids: List[int]
