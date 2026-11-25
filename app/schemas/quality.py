
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class QualityCreate(BaseModel):

    batch_id: int

    moisture_reading: Optional[float] = Field(
        default=None,
        ge=0
    )

    result: str = Field(
        min_length=1,
        max_length=30
    )

    tested_at: datetime


class QualityUpdate(BaseModel):

    moisture_reading: Optional[float] = Field(
        default=None,
        ge=0
    )

    result: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=30
    )

    tested_at: Optional[datetime] = None


class QualityResponse(BaseModel):

    id: int
    batch_id: int
    moisture_reading: Optional[float]
    result: str
    tested_at: datetime
    entered_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
