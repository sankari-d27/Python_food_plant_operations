
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


# CREATE PRODUCTION LINE
class ProductionLineCreate(BaseModel):

    line_code: str = Field(
        min_length=1,
        max_length=20
    )

    line_name: str = Field(
        min_length=1,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255
    )

    is_active: bool = True


# UPDATE PRODUCTION LINE
class ProductionLineUpdate(BaseModel):

    line_code: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=20
    )

    line_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255
    )

    is_active: Optional[bool] = None


# PRODUCTION LINE RESPONSE
class ProductionLineResponse(BaseModel):

    id: int
    line_code: str
    line_name: str
    description: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
