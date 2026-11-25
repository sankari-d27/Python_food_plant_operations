
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db

from app.schemas.production import (
    ProductionCreate,
    ProductionUpdate,
    ProductionResponse
)

from app.services.production_service import ProductionService


router = APIRouter(
    prefix="/production",
    tags=["Production Management"]
)


# CREATE PRODUCTION RECORD
@router.post("/", response_model=ProductionResponse)
def create_production(
    production: ProductionCreate,
    db: Session = Depends(get_db)
):

    service = ProductionService(db)

    try:
        return service.create_production(
            production.model_dump()
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Production record creation failed"
        ) from exc


# VIEW ALL PRODUCTION RECORDS
@router.get("/", response_model=list[ProductionResponse])
def get_productions(
    db: Session = Depends(get_db)
):

    service = ProductionService(db)

    return service.get_productions()


# VIEW SINGLE PRODUCTION RECORD
@router.get(
    "/{production_id}",
    response_model=ProductionResponse
)
def get_production(
    production_id: int,
    db: Session = Depends(get_db)
):

    service = ProductionService(db)

    try:
        return service.get_production_by_id(production_id)

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc


# UPDATE PRODUCTION RECORD
@router.put(
    "/{production_id}",
    response_model=ProductionResponse
)
def update_production(
    production_id: int,
    production: ProductionUpdate,
    db: Session = Depends(get_db)
):

    service = ProductionService(db)

    update_data = production.model_dump(
        exclude_unset=True
    )

    try:
        return service.update_production(
            production_id=production_id,
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
            detail="Production record update failed"
        ) from exc


# DELETE PRODUCTION RECORD
@router.delete("/{production_id}")
def delete_production(
    production_id: int,
    db: Session = Depends(get_db)
):

    service = ProductionService(db)

    try:
        return service.delete_production(
            production_id=production_id
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
            detail="Production record deletion failed"
        ) from exc
