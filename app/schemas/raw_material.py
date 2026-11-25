
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


# CREATE RAW MATERIAL
class RawMaterialCreate(BaseModel):

    material_code: str = Field(min_length=1, max_length=50)

    material_name: str = Field(min_length=1, max_length=100)

    supplier_id: int = Field(gt=0)

    available_quantity: float = Field(default=0.0, ge=0)

    unit: str = Field(min_length=1, max_length=20)

    is_active: bool = True


# UPDATE RAW MATERIAL
class RawMaterialUpdate(BaseModel):

    material_code: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    material_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    supplier_id: Optional[int] = Field(default=None, gt=0)

    available_quantity: Optional[float] = Field(
        default=None,
        ge=0
    )

    unit: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=20
    )

    is_active: Optional[bool] = None


# RAW MATERIAL RESPONSE
class RawMaterialResponse(BaseModel):

    id: int
    material_code: str
    material_name: str
    supplier_id: int
    available_quantity: float
    unit: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
