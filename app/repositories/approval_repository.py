
from app.models.approval import Approval
from app.repositories.base_repository import BaseRepository


class ApprovalRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(db, Approval)

    def get_by_batch_id(self, batch_id):
        return (
            self.db.query(Approval)
            .filter(Approval.batch_id == batch_id)
            .order_by(Approval.created_at.desc())
            .all()
        )

    def get_by_reviewer(self, reviewer_id):
        return (
            self.db.query(Approval)
            .filter(Approval.reviewed_by == reviewer_id)
            .order_by(Approval.created_at.desc())
            .all()
        )

    def get_by_decision(self, decision):
        return (
            self.db.query(Approval)
            .filter(Approval.decision == decision)
            .order_by(Approval.created_at.desc())
            .all()
        )
