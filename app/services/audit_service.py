
import json
from sqlalchemy.orm import Session

from app.repositories.audit_repository import AuditRepository


class AuditService:

    def __init__(self):
        self.repository = AuditRepository()

    def log_action(
        self,
        db: Session,
        user_id: int = None,
        action: str = None,
        entity_type: str = None,
        entity_id: int = None,
        old_value=None,
        new_value=None,
        commit=True
    ):

        if not action or not entity_type:
            raise ValueError("Action and entity_type are required")

        data = {
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_value": json.dumps(old_value, default=str)
                if old_value is not None else None,
            "new_value": json.dumps(new_value, default=str)
                if new_value is not None else None
        }

        return self.repository.create(
            db=db,
            data=data,
            commit=commit
        )

    def get_all_logs(self, db: Session):
        return self.repository.get_all(db)

    def get_entity_logs(self, db: Session, entity_type: str):
        return self.repository.get_by_entity(db, entity_type)

    def get_user_logs(self, db: Session, user_id: int):
        return self.repository.get_by_user(db, user_id)
