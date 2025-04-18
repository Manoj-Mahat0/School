from sqlalchemy import Column, Integer, ForeignKey
from db.database import Base

class ClassFeeStructure(Base):
    __tablename__ = "class_fee_structure"
    id = Column(Integer, primary_key=True, index=True)
    class_section_id = Column(Integer, ForeignKey("class_sections.id"), unique=True)
    tuition_fee = Column(Integer, default=0)
    exam_fee = Column(Integer, default=0)
    library_fee = Column(Integer, default=0)
    transport_fee = Column(Integer, default=0)
