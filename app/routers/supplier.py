
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.supplier import (
    SupplierCreate,
    SupplierUpdate,
    SupplierResponse
)
from app.services.supplier_service import SupplierService


router = APIRouter(
    prefix="/suppliers",
    tags=["Supplier Management"]
)


def get_supplier_service(db: Session = Depends(get_db)):
    return SupplierService(db)


# CREATE SUPPLIER
@router.post("/", response_model=SupplierResponse)
def create_supplier(
    supplier: SupplierCreate,
    service: SupplierService = Depends(get_supplier_service)
):
    try:
        return service.create_supplier(
            supplier.model_dump()
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# GET ALL SUPPLIERS
@router.get("/", response_model=list[SupplierResponse])
def get_suppliers(
    service: SupplierService = Depends(get_supplier_service)
):
    return service.get_suppliers()


# GET SUPPLIER BY ID
@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    service: SupplierService = Depends(get_supplier_service)
):
    try:
        return service.get_supplier_by_id(supplier_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))


# UPDATE SUPPLIER
@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    service: SupplierService = Depends(get_supplier_service)
):
    try:
        return service.update_supplier(
            supplier_id,
            supplier_data.model_dump(exclude_unset=True)
        )
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# DELETE SUPPLIER
@router.delete("/{supplier_id}")
def delete_supplier(
    supplier_id: int,
    service: SupplierService = Depends(get_supplier_service)
):
    try:
        return service.delete_supplier(supplier_id)
    except LookupError as e:
        raise HTTPException(status_code=404, detail=str(e))
