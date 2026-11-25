
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database import Base
from datetime import datetime


class Approval(Base):
    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)

    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)

    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)

    decision = Column(String(30), default="pending")

    comments = Column(String(500), nullable=True)

    reviewed_at = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
