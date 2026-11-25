
from datetime import datetime
from typing import Optional, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


ApprovalDecision = Literal["pending", "approved", "rejected"]


class ApprovalBase(BaseModel):

    batch_id: int = Field(..., gt=0)

    reviewed_by: Optional[int] = Field(
        default=None,
        gt=0
    )

    decision: ApprovalDecision = "pending"

    comments: Optional[str] = Field(
        default=None,
        max_length=500
    )

    reviewed_at: Optional[datetime] = None

    @field_validator("comments")
    @classmethod
    def validate_comments(cls, value):
        if value is not None:
            value = value.strip()

            if not value:
                return None

            if len(value) > 500:
                raise ValueError(
                    "Comments cannot exceed 500 characters"
                )

        return value

    @field_validator("decision", mode="before")
    @classmethod
    def normalize_decision(cls, value):
        if isinstance(value, str):
            return value.strip().lower()

        return value


class ApprovalCreate(ApprovalBase):
    pass


class ApprovalUpdate(BaseModel):

    batch_id: Optional[int] = Field(default=None, gt=0)

    reviewed_by: Optional[int] = Field(
        default=None,
        gt=0
    )

    decision: Optional[ApprovalDecision] = None

    comments: Optional[str] = Field(
        default=None,
        max_length=500
    )

    reviewed_at: Optional[datetime] = None

    @field_validator("comments")
    @classmethod
    def validate_comments(cls, value):
        if value is not None:
            value = value.strip()

            if not value:
                return None

            if len(value) > 500:
                raise ValueError(
                    "Comments cannot exceed 500 characters"
                )

        return value

    @field_validator("decision", mode="before")
    @classmethod
    def normalize_decision(cls, value):
        if isinstance(value, str):
            return value.strip().lower()

        return value


class ApprovalResponse(ApprovalBase):

    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
