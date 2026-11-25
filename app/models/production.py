
from sqlalchemy import Column, Integer, Float, Date, String, ForeignKey
from app.database import Base


class Production(Base):
    __tablename__ = "production_records"

    id = Column(Integer, primary_key=True, index=True)

    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)

    production_date = Column(Date, nullable=False)

    input_quantity = Column(Float, nullable=False)
    output_quantity = Column(Float, nullable=False)
    wastage_quantity = Column(Float, default=0.0)

    shift = Column(String(20), nullable=False)
