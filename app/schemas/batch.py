
from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# CREATE BATCH
class BatchCreate(BaseModel):

    batch_number: str = Field(
        min_length=1,
        max_length=50
    )

    product_id: int = Field(gt=0)

    production_line_id: int = Field(gt=0)

    created_by: int = Field(gt=0)

    production_date: date

    input_quantity: float = Field(ge=0)

    output_quantity: float = Field(ge=0)

    status: str = Field(
        default="draft",
        max_length=30
    )


# UPDATE BATCH
class BatchUpdate(BaseModel):

    batch_number: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    product_id: Optional[int] = Field(
        default=None,
        gt=0
    )

    production_line_id: Optional[int] = Field(
        default=None,
        gt=0
    )

    production_date: Optional[date] = None

    input_quantity: Optional[float] = Field(
        default=None,
        ge=0
    )

    output_quantity: Optional[float] = Field(
        default=None,
        ge=0
    )

    status: Optional[str] = Field(
        default=None,
        max_length=30
    )


# BATCH RESPONSE
class BatchResponse(BaseModel):

    id: int

    batch_number: str

    product_id: int

    production_line_id: int

    created_by: int

    production_date: date

    input_quantity: float

    output_quantity: float

    status: Optional[str] = None

    model_config = ConfigDict(
        from_attributes=True
    )
