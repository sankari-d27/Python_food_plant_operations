
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


# CREATE PRODUCT
class ProductCreate(BaseModel):

    product_code: str = Field(
        min_length=1,
        max_length=50
    )

    product_name: str = Field(
        min_length=1,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255
    )

    unit: Optional[str] = Field(
        default=None,
        max_length=30
    )

    is_active: bool = True


# UPDATE PRODUCT
class ProductUpdate(BaseModel):

    product_code: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    product_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    description: Optional[str] = Field(
        default=None,
        max_length=255
    )

    unit: Optional[str] = Field(
        default=None,
        max_length=30
    )

    is_active: Optional[bool] = None


# PRODUCT RESPONSE
class ProductResponse(BaseModel):

    id: int
    product_code: str
    product_name: str
    description: Optional[str] = None
    unit: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(
        from_attributes=True
    )
