from pydantic import BaseModel

class ClassFeeCreateUpdate(BaseModel):
    class_section_id: int
    tuition_fee: int
    exam_fee: int
    library_fee: int
    transport_fee: int
