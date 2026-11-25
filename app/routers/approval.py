
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth import require_roles

from app.schemas.approval import (
    ApprovalCreate,
    ApprovalUpdate,
    ApprovalResponse
)

from app.services.approval_service import ApprovalService


router = APIRouter(
    prefix="/approvals",
    tags=["Approval Management"]
)


# CREATE APPROVAL - ADMIN ONLY
@router.post(
    "/",
    response_model=ApprovalResponse,
    dependencies=[Depends(require_roles("admin"))]
)
def create_approval(
    approval: ApprovalCreate,
    db: Session = Depends(get_db)
):
    service = ApprovalService(db)

    try:
        return service.create_approval(
            approval.model_dump(exclude_unset=True)
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Approval creation failed"
        ) from exc


# GET ALL APPROVALS - ADMIN ONLY
@router.get(
    "/",
    response_model=list[ApprovalResponse],
    dependencies=[Depends(require_roles("admin"))]
)
def get_approvals(
    db: Session = Depends(get_db)
):
    service = ApprovalService(db)
    return service.get_approvals()


# GET APPROVALS BY BATCH - ADMIN ONLY
@router.get(
    "/batch/{batch_id}",
    response_model=list[ApprovalResponse],
    dependencies=[Depends(require_roles("admin"))]
)
def get_approvals_by_batch(
    batch_id: int,
    db: Session = Depends(get_db)
):
    service = ApprovalService(db)

    try:
        return service.get_approvals_by_batch(batch_id)

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc)
        ) from exc


# GET APPROVAL BY ID - ADMIN ONLY
@router.get(
    "/{approval_id}",
    response_model=ApprovalResponse,
    dependencies=[Depends(require_roles("admin"))]
)
def get_approval(
    approval_id: int,
    db: Session = Depends(get_db)
):
    service = ApprovalService(db)

    try:
        return service.get_approval_by_id(approval_id)

    except LookupError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc)
        ) from exc


# UPDATE APPROVAL - ADMIN ONLY
@router.put(
    "/{approval_id}",
    response_model=ApprovalResponse,
    dependencies=[Depends(require_roles("admin"))]
)
def update_approval(
    approval_id: int,
    approval: ApprovalUpdate,
    db: Session = Depends(get_db)
):
    service = ApprovalService(db)

    update_data = approval.model_dump(exclude_unset=True)

    try:
        return service.update_approval(
            approval_id=approval_id,
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
            detail="Approval update failed"
        ) from exc


# DELETE APPROVAL - ADMIN ONLY
@router.delete(
    "/{approval_id}",
    dependencies=[Depends(require_roles("admin"))]
)
def delete_approval(
    approval_id: int,
    db: Session = Depends(get_db)
):
    service = ApprovalService(db)

    try:
        return service.delete_approval(approval_id)

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
            detail="Approval deletion failed"
        ) from exc
