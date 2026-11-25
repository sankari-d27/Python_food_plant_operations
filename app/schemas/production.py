
from pydantic import BaseModel, ConfigDict, Field
from datetime import date
from typing import Optional


# CREATE PRODUCTION
class ProductionCreate(BaseModel):

    batch_id: int

    production_date: date

    input_quantity: float = Field(ge=0)

    output_quantity: float = Field(ge=0)

    wastage_quantity: float = Field(default=0, ge=0)

    shift: str


# UPDATE PRODUCTION
class ProductionUpdate(BaseModel):

    production_date: Optional[date] = None

    input_quantity: Optional[float] = Field(
        default=None, ge=0
    )

    output_quantity: Optional[float] = Field(
        default=None, ge=0
    )

    wastage_quantity: Optional[float] = Field(
        default=None, ge=0
    )

    shift: Optional[str] = None


# PRODUCTION RESPONSE
class ProductionResponse(BaseModel):

    id: int

    batch_id: int

    production_date: date

    input_quantity: float

    output_quantity: float

    wastage_quantity: float

    shift: str

    model_config = ConfigDict(from_attributes=True)
