
from pydantic import BaseModel, ConfigDict, Field
from typing import Optional


# CREATE MACHINE
class MachineCreate(BaseModel):

    machine_code: str = Field(
        min_length=1,
        max_length=50
    )

    machine_name: str = Field(
        min_length=1,
        max_length=100
    )

    production_line_id: int = Field(gt=0)

    machine_status: str = "available"

    is_active: bool = True


# UPDATE MACHINE
class MachineUpdate(BaseModel):

    machine_code: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=50
    )

    machine_name: Optional[str] = Field(
        default=None,
        min_length=1,
        max_length=100
    )

    production_line_id: Optional[int] = Field(
        default=None,
        gt=0
    )

    machine_status: Optional[str] = None

    is_active: Optional[bool] = None


# MACHINE RESPONSE
class MachineResponse(BaseModel):

    id: int
    machine_code: str
    machine_name: str
    production_line_id: int
    machine_status: str
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
