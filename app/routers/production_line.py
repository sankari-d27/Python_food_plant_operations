
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.production_line_service import ProductionLineService
from app.schemas.production_line import (
    ProductionLineCreate,
    ProductionLineUpdate,
    ProductionLineResponse
)


router = APIRouter(
    prefix="/production-lines",
    tags=["Production Line Management"]
)


# CREATE PRODUCTION LINE
@router.post("/", response_model=ProductionLineResponse)
def create_production_line(
    line_data: ProductionLineCreate,
    db: Session = Depends(get_db)
):

    service = ProductionLineService(db)

    try:
        return service.create_production_line(
            line_data.model_dump()
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# GET ALL PRODUCTION LINES
@router.get("/", response_model=list[ProductionLineResponse])
def get_production_lines(
    db: Session = Depends(get_db)
):

    service = ProductionLineService(db)

    return service.get_production_lines()


# GET PRODUCTION LINE BY ID
@router.get("/{line_id}", response_model=ProductionLineResponse)
def get_production_line(
    line_id: int,
    db: Session = Depends(get_db)
):

    service = ProductionLineService(db)

    try:
        return service.get_production_line_by_id(line_id)

    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


# UPDATE PRODUCTION LINE
@router.put("/{line_id}", response_model=ProductionLineResponse)
def update_production_line(
    line_id: int,
    line_data: ProductionLineUpdate,
    db: Session = Depends(get_db)
):

    service = ProductionLineService(db)

    try:
        return service.update_production_line(
            line_id,
            line_data.model_dump(exclude_unset=True)
        )

    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# DELETE PRODUCTION LINE
@router.delete("/{line_id}")
def delete_production_line(
    line_id: int,
    db: Session = Depends(get_db)
):

    service = ProductionLineService(db)

    try:
        return service.delete_production_line(line_id)

    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
