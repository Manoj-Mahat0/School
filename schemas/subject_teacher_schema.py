from pydantic import BaseModel

class SubjectTeacherAssign(BaseModel):
    subject_id: int
    teacher_id: int
    class_section_id: int
