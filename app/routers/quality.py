
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.quality import (
    QualityCreate,
    QualityUpdate,
    QualityResponse
)

from app.services.quality_service import QualityService


router = APIRouter(
    prefix="/quality",
    tags=["Quality Management"]
)


# CREATE QUALITY TEST
@router.post("/", response_model=QualityResponse)
def create_quality(
    quality: QualityCreate,
    db: Session = Depends(get_db)
):

    service = QualityService(db)

    try:
        return service.create_quality(
            quality.model_dump()
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Quality test creation failed"
        ) from exc


# VIEW ALL QUALITY TESTS
@router.get("/", response_model=list[QualityResponse])
def get_all_quality(
    db: Session = Depends(get_db)
):

    service = QualityService(db)

    return service.get_all_quality()


# VIEW SINGLE QUALITY TEST
@router.get(
    "/{quality_id}",
    response_model=QualityResponse
)
def get_quality(
    quality_id: int,
    db: Session = Depends(get_db)
):

    service = QualityService(db)

    try:
        return service.get_quality_by_id(quality_id)

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc


# UPDATE QUALITY TEST
@router.put(
    "/{quality_id}",
    response_model=QualityResponse
)
def update_quality(
    quality_id: int,
    quality: QualityUpdate,
    db: Session = Depends(get_db)
):

    service = QualityService(db)

    update_data = quality.model_dump(
        exclude_unset=True
    )

    try:
        return service.update_quality(
            quality_id=quality_id,
            data=update_data
        )

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Quality test update failed"
        ) from exc


# DELETE QUALITY TEST
@router.delete("/{quality_id}")
def delete_quality(
    quality_id: int,
    db: Session = Depends(get_db)
):

    service = QualityService(db)

    try:
        return service.delete_quality(quality_id)

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Quality test deletion failed"
        ) from exc
