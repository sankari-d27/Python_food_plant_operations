
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.audit_service import AuditService
from app.schemas.audit import AuditLogResponse

router = APIRouter(
    prefix="/audit",
    tags=["Audit Trail"]
)

service = AuditService()


@router.get("/", response_model=list[AuditLogResponse])
def get_all_logs(db: Session = Depends(get_db)):
    return service.get_all_logs(db)


@router.get("/entity/{entity_type}", response_model=list[AuditLogResponse])
def get_entity_logs(
    entity_type: str,
    db: Session = Depends(get_db)
):
    return service.get_entity_logs(db, entity_type)


@router.get("/user/{user_id}", response_model=list[AuditLogResponse])
def get_user_logs(
    user_id: int,
    db: Session = Depends(get_db)
):
    return service.get_user_logs(db, user_id)
