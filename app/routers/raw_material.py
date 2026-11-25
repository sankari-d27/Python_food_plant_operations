
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.raw_material_service import RawMaterialService
from app.schemas.raw_material import (
    RawMaterialCreate,
    RawMaterialUpdate,
    RawMaterialResponse
)


router = APIRouter(
    prefix="/raw-materials",
    tags=["Raw Material Management"]
)


# CREATE RAW MATERIAL
@router.post("/", response_model=RawMaterialResponse)
def create_raw_material(
    data: RawMaterialCreate,
    db: Session = Depends(get_db)
):
    service = RawMaterialService(db)

    try:
        return service.create_raw_material(
            data.model_dump()
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# GET ALL RAW MATERIALS
@router.get("/", response_model=list[RawMaterialResponse])
def get_raw_materials(
    db: Session = Depends(get_db)
):
    service = RawMaterialService(db)

    return service.get_raw_materials()


# GET RAW MATERIAL BY ID
@router.get("/{material_id}", response_model=RawMaterialResponse)
def get_raw_material_by_id(
    material_id: int,
    db: Session = Depends(get_db)
):
    service = RawMaterialService(db)

    try:
        return service.get_raw_material_by_id(material_id)

    except LookupError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


# UPDATE RAW MATERIAL
@router.put("/{material_id}", response_model=RawMaterialResponse)
def update_raw_material(
    material_id: int,
    data: RawMaterialUpdate,
    db: Session = Depends(get_db)
):
    service = RawMaterialService(db)

    try:
        return service.update_raw_material(
            material_id,
            data.model_dump(exclude_unset=True)
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


# DELETE RAW MATERIAL
@router.delete("/{material_id}")
def delete_raw_material(
    material_id: int,
    db: Session = Depends(get_db)
):
    service = RawMaterialService(db)

    try:
        return service.delete_raw_material(material_id)

    except LookupError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
