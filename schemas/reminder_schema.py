from pydantic import BaseModel

class ReminderRequest(BaseModel):
    class_section_id: int
