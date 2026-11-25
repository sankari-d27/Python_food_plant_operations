
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from app.database import Base
from datetime import datetime


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    action = Column(String(50), nullable=False)

    entity_type = Column(String(100), nullable=False)

    entity_id = Column(Integer, nullable=True)

    old_value = Column(Text, nullable=True)

    new_value = Column(Text, nullable=True)

    timestamp = Column(DateTime, default=datetime.utcnow)
