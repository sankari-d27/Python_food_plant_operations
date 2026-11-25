
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.database import get_db

from app.schemas.product import (
    ProductCreate,
    ProductUpdate,
    ProductResponse
)

from app.services.product_service import ProductService


router = APIRouter(
    prefix="/products",
    tags=["Product Management"]
)


# CREATE PRODUCT
@router.post("/", response_model=ProductResponse, status_code=201)
def create_product(
    product: ProductCreate,
    db: Session = Depends(get_db)
):

    service = ProductService(db)

    try:
        return service.create_product(
            product.model_dump()
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Product code already exists or database constraint failed"
        )


# GET ALL PRODUCTS
@router.get("/", response_model=list[ProductResponse])
def get_products(
    db: Session = Depends(get_db)
):

    service = ProductService(db)

    return service.get_products()


# GET PRODUCT BY ID
@router.get("/{product_id}", response_model=ProductResponse)
def get_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    service = ProductService(db)

    try:
        return service.get_product_by_id(product_id)

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


# UPDATE PRODUCT
@router.put("/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: int,
    product_data: ProductUpdate,
    db: Session = Depends(get_db)
):

    service = ProductService(db)

    try:
        update_data = product_data.model_dump(
            exclude_unset=True
        )

        return service.update_product(
            product_id,
            update_data
        )

    except ValueError as e:
        status_code = (
            404 if str(e) == "Product not found" else 400
        )

        raise HTTPException(
            status_code=status_code,
            detail=str(e)
        )

    except IntegrityError:
        raise HTTPException(
            status_code=409,
            detail="Product code already exists or database constraint failed"
        )


# DELETE PRODUCT
@router.delete("/{product_id}")
def delete_product(
    product_id: int,
    db: Session = Depends(get_db)
):

    service = ProductService(db)

    try:
        return service.delete_product(product_id)

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
