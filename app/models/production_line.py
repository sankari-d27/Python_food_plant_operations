
from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class ProductionLine(Base):
    __tablename__ = "production_lines"

    id = Column(Integer, primary_key=True, index=True)
    line_code = Column(String(20), unique=True, nullable=False)
    line_name = Column(String(100), nullable=False)
    description = Column(String(255))

    is_active = Column(Boolean, default=True)
