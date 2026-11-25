
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.user import User
from app.models.approval import Approval

from app.repositories.approval_repository import ApprovalRepository
from app.services.audit_helper import record_audit


class ApprovalService:

    VALID_DECISIONS = {
        "pending",
        "approved",
        "rejected"
    }

    def __init__(self, db: Session):

        self.db = db
        self.repository = ApprovalRepository(db)

    # APPROVAL SNAPSHOT
    def _approval_snapshot(self, approval):

        return {
            "id": approval.id,
            "batch_id": approval.batch_id,
            "reviewed_by": approval.reviewed_by,
            "decision": approval.decision,
            "comments": approval.comments,
            "reviewed_at": (
                approval.reviewed_at.isoformat()
                if approval.reviewed_at else None
            ),
            "created_at": (
                approval.created_at.isoformat()
                if approval.created_at else None
            )
        }

    # VALIDATE DECISION
    def _validate_decision(self, decision):

        if not isinstance(decision, str):
            raise ValueError("Decision must be text")

        decision = decision.strip().lower()

        if decision not in self.VALID_DECISIONS:
            raise ValueError(
                "Invalid decision. Allowed decisions: "
                "pending, approved, rejected"
            )

        return decision

    # VALIDATE COMMENTS
    def _validate_comments(self, comments):

        if comments is None:
            return None

        if not isinstance(comments, str):
            raise ValueError("Comments must be text")

        comments = comments.strip()

        if len(comments) > 500:
            raise ValueError(
                "Comments cannot exceed 500 characters"
            )

        return comments if comments else None

    # VALIDATE BATCH
    def _validate_batch(self, batch_id):

        batch = (
            self.db.query(Batch)
            .filter(Batch.id == batch_id)
            .first()
        )

        if not batch:
            raise ValueError("Batch does not exist")

        return batch

    # VALIDATE REVIEWER
    def _validate_reviewer(self, reviewer_id):

        if reviewer_id is None:
            return None

        reviewer = (
            self.db.query(User)
            .filter(User.id == reviewer_id)
            .first()
        )

        if not reviewer:
            raise ValueError("Reviewer user does not exist")

        return reviewer

    # CREATE APPROVAL
    def create_approval(self, data: dict, user_id=None):

        data = dict(data)

        allowed_fields = {
            "batch_id",
            "reviewed_by",
            "decision",
            "comments",
            "reviewed_at"
        }

        invalid_fields = set(data.keys()) - allowed_fields

        if invalid_fields:
            raise ValueError(
                f"Invalid fields: {', '.join(invalid_fields)}"
            )

        if data.get("batch_id") is None:
            raise ValueError("Batch ID is required")

        if data.get("reviewed_at") is not None:
            raise ValueError(
                "Review timestamp is managed automatically"
            )

        data["decision"] = self._validate_decision(
            data.get("decision", "pending")
        )

        if data["decision"] != "pending":
            raise ValueError(
                "New approvals must start with pending decision"
            )

        self._validate_batch(data["batch_id"])

        data["comments"] = self._validate_comments(
            data.get("comments")
        )

        if data.get("reviewed_by") is not None:
            self._validate_reviewer(data["reviewed_by"])

        data["reviewed_at"] = None

        try:

            approval = self.repository.create(
                data,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=user_id,
                action="CREATE",
                entity_type="Approval",
                entity_id=approval.id,
                new_value=self._approval_snapshot(approval),
                commit=False
            )

            self.db.commit()
            self.db.refresh(approval)

            return approval

        except Exception:
            self.db.rollback()
            raise

    # GET ALL APPROVALS
    def get_approvals(self):

        return self.repository.get_all()

    # GET APPROVAL BY ID
    def get_approval_by_id(self, approval_id: int):

        approval = self.repository.get_by_id(approval_id)

        if not approval:
            raise LookupError("Approval not found")

        return approval

    # GET APPROVALS BY BATCH
    def get_approvals_by_batch(self, batch_id: int):

        self._validate_batch(batch_id)

        return self.repository.get_by_batch_id(batch_id)

    # GET APPROVALS BY REVIEWER
    def get_approvals_by_reviewer(self, reviewer_id: int):

        self._validate_reviewer(reviewer_id)

        return self.repository.get_by_reviewer(reviewer_id)

    # GET APPROVALS BY DECISION
    def get_approvals_by_decision(self, decision: str):

        decision = self._validate_decision(decision)

        return self.repository.get_by_decision(decision)

    # UPDATE APPROVAL
    def update_approval(
        self,
        approval_id: int,
        data: dict,
        user_id=None
    ):

        approval = self.get_approval_by_id(approval_id)

        # Finalized approvals cannot be modified.
        if approval.decision in {"approved", "rejected"}:
            raise ValueError(
                "Finalized approvals cannot be modified"
            )

        data = dict(data)

        allowed_fields = {
            "decision",
            "reviewed_by",
            "comments"
        }

        invalid_fields = set(data.keys()) - allowed_fields

        if invalid_fields:
            raise ValueError(
                f"Fields cannot be updated: "
                f"{', '.join(invalid_fields)}"
            )

        if not data:
            return approval

        if "decision" in data:
            data["decision"] = self._validate_decision(
                data["decision"]
            )

        if "comments" in data:
            data["comments"] = self._validate_comments(
                data["comments"]
            )

        if (
            "reviewed_by" in data
            and data["reviewed_by"] is not None
        ):
            self._validate_reviewer(data["reviewed_by"])

        old_value = self._approval_snapshot(approval)

        # Determine the final reviewer and review timestamp.
        new_decision = data.get(
            "decision",
            approval.decision
        )

        if new_decision in {"approved", "rejected"}:

            reviewer_id = (
                data.get("reviewed_by")
                or user_id
                or approval.reviewed_by
            )

            if reviewer_id is None:
                raise ValueError(
                    "Reviewer is required to finalize approval"
                )

            self._validate_reviewer(reviewer_id)

            data["reviewed_by"] = reviewer_id
            data["reviewed_at"] = datetime.utcnow()

        has_changes = any(
            getattr(approval, key) != value
            for key, value in data.items()
        )

        if not has_changes:
            return approval

        try:

            updated_approval = self.repository.update(
                approval_id,
                data,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=user_id,
                action="UPDATE",
                entity_type="Approval",
                entity_id=approval_id,
                old_value=old_value,
                new_value=self._approval_snapshot(
                    updated_approval
                ),
                commit=False
            )

            self.db.commit()
            self.db.refresh(updated_approval)

            return updated_approval

        except Exception:
            self.db.rollback()
            raise

    # DELETE APPROVAL
    def delete_approval(self, approval_id: int, user_id=None):

        approval = self.get_approval_by_id(approval_id)

        raise ValueError(
            "Approval records cannot be deleted. "
            "They are permanent food production traceability records."
        )
