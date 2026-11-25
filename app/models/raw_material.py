
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey
from app.database import Base


class RawMaterial(Base):
    __tablename__ = "raw_materials"

    id = Column(Integer, primary_key=True, index=True)

    material_code = Column(String(50), unique=True, nullable=False)
    material_name = Column(String(100), nullable=False)

    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False)

    available_quantity = Column(Float, default=0.0)
    unit = Column(String(20), nullable=False)

    is_active = Column(Boolean, default=True)
