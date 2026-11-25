
from sqlalchemy import Column, Integer, String, Boolean
from app.database import Base


class Machine(Base):
    __tablename__ = "machines"

    id = Column(Integer, primary_key=True, index=True)

    machine_code = Column(String(50), unique=True, nullable=False)
    machine_name = Column(String(100), nullable=False)

    production_line_id = Column(Integer, nullable=False)

    machine_status = Column(String(30), default="available")

    is_active = Column(Boolean, default=True)
