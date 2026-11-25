
from sqlalchemy import (
    Column,
    Integer,
    String,
    Float,
    Date,
    ForeignKey
)
from app.database import Base


class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)

    # Batch number is not globally unique because
    # historical imports may contain reused numbers.
    batch_number = Column(String(50), nullable=False, index=True)

    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    production_line_id = Column(
        Integer,
        ForeignKey("production_lines.id"),
        nullable=False
    )

    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    production_date = Column(Date, nullable=False)

    input_quantity = Column(Float, nullable=False)
    output_quantity = Column(Float, nullable=False)

    status = Column(String(30), default="draft")
