
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.machine_service import MachineService
from app.schemas.machine import (
    MachineCreate,
    MachineUpdate,
    MachineResponse
)


router = APIRouter(
    prefix="/machines",
    tags=["Machine Management"]
)


# CREATE MACHINE
@router.post("/", response_model=MachineResponse)
def create_machine(
    machine_data: MachineCreate,
    db: Session = Depends(get_db)
):

    service = MachineService(db)

    try:
        return service.create_machine(
            machine_data.model_dump()
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )


# GET ALL MACHINES
@router.get("/", response_model=list[MachineResponse])
def get_machines(
    db: Session = Depends(get_db)
):

    service = MachineService(db)

    return service.get_machines()


# GET MACHINE BY ID
@router.get("/{machine_id}", response_model=MachineResponse)
def get_machine(
    machine_id: int,
    db: Session = Depends(get_db)
):

    service = MachineService(db)

    try:
        return service.get_machine_by_id(machine_id)

    except LookupError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )


# UPDATE MACHINE
@router.put("/{machine_id}", response_model=MachineResponse)
def update_machine(
    machine_id: int,
    machine_data: MachineUpdate,
    db: Session = Depends(get_db)
):

    service = MachineService(db)

    try:
        return service.update_machine(
            machine_id,
            machine_data.model_dump(exclude_unset=True)
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


# DELETE MACHINE
@router.delete("/{machine_id}")
def delete_machine(
    machine_id: int,
    db: Session = Depends(get_db)
):

    service = MachineService(db)

    try:
        return service.delete_machine(machine_id)

    except LookupError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
