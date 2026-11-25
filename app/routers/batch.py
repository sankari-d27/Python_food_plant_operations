
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.services.batch_service import BatchService

from app.schemas.batch import (
    BatchCreate,
    BatchUpdate,
    BatchResponse
)


router = APIRouter(
    prefix="/batches",
    tags=["Batch Management"]
)


# CREATE BATCH
@router.post("/", response_model=BatchResponse)
def create_batch(
    batch_data: BatchCreate,
    db: Session = Depends(get_db)
):

    service = BatchService(db)

    try:
        return service.create_batch(
            batch_data.model_dump()
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# GET ALL BATCHES
@router.get("/", response_model=list[BatchResponse])
def get_batches(
    db: Session = Depends(get_db)
):

    service = BatchService(db)

    return service.get_batches()


# GET BATCH BY ID
@router.get("/{batch_id}", response_model=BatchResponse)
def get_batch(
    batch_id: int,
    db: Session = Depends(get_db)
):

    service = BatchService(db)

    try:
        return service.get_batch_by_id(batch_id)

    except LookupError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


# UPDATE BATCH
@router.put("/{batch_id}", response_model=BatchResponse)
def update_batch(
    batch_id: int,
    batch_data: BatchUpdate,
    db: Session = Depends(get_db)
):

    service = BatchService(db)

    try:
        return service.update_batch(
            batch_id,
            batch_data.model_dump(exclude_unset=True)
        )

    except LookupError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# DELETE BATCH
@router.delete("/{batch_id}")
def delete_batch(
    batch_id: int,
    db: Session = Depends(get_db)
):

    service = BatchService(db)

    try:
        return service.delete_batch(batch_id)

    except LookupError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
