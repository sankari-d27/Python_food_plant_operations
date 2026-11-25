
from sqlalchemy import Column, Integer, Float, String, DateTime, ForeignKey
from app.database import Base
from datetime import datetime


class QualityTest(Base):
    __tablename__ = "quality_tests"

    id = Column(Integer, primary_key=True, index=True)

    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=False)

    moisture_reading = Column(Float, nullable=True)

    result = Column(String(30), nullable=False)

    # Actual time when the test was performed.
    tested_at = Column(DateTime, nullable=False)

    # Time when the result was entered into the application.
    entered_at = Column(DateTime, default=datetime.utcnow)
