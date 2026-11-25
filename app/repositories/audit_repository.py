
from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


class AuditRepository:

    def create(self, db: Session, data: dict, commit=True):

        audit = AuditLog(**data)

        db.add(audit)
        db.flush()
        db.refresh(audit)

        if commit:
            db.commit()

        return audit

    def get_all(self, db: Session):

        return (
            db.query(AuditLog)
            .order_by(AuditLog.timestamp.desc())
            .all()
        )

    def get_by_entity(self, db: Session, entity_type: str):

        return (
            db.query(AuditLog)
            .filter(AuditLog.entity_type == entity_type)
            .order_by(AuditLog.timestamp.desc())
            .all()
        )

    def get_by_user(self, db: Session, user_id: int):

        return (
            db.query(AuditLog)
            .filter(AuditLog.user_id == user_id)
            .order_by(AuditLog.timestamp.desc())
            .all()
        )
