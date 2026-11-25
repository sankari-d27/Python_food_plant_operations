
from sqlalchemy.orm import Session

from app.services.audit_service import AuditService


audit_service = AuditService()


def record_audit(
    db: Session,
    user_id: int = None,
    action: str = None,
    entity_type: str = None,
    entity_id: int = None,
    old_value=None,
    new_value=None,
    commit=True
):
    return audit_service.log_action(
        db=db,
        user_id=user_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value,
        new_value=new_value,
        commit=commit
    )
