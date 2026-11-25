
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.repositories.quality_repository import QualityRepository
from app.services.audit_helper import record_audit


class QualityService:

    VALID_RESULTS = {"pass", "fail", "pending"}

    def __init__(self, db: Session):

        self.db = db
        self.repository = QualityRepository(db)

    def _quality_snapshot(self, quality):

        return {
            "id": quality.id,
            "batch_id": quality.batch_id,
            "moisture_reading": quality.moisture_reading,
            "result": quality.result,
            "tested_at": (
                quality.tested_at.isoformat()
                if quality.tested_at else None
            ),
            "entered_at": (
                quality.entered_at.isoformat()
                if quality.entered_at else None
            )
        }

    def _validate_batch(self, batch_id):

        batch = (
            self.db.query(Batch)
            .filter(Batch.id == batch_id)
            .first()
        )

        if not batch:
            raise ValueError("Batch does not exist")

    def _validate_result(self, result):

        if not isinstance(result, str):
            raise ValueError("Quality result must be text")

        result = result.strip().lower()

        if result not in self.VALID_RESULTS:
            raise ValueError(
                "Invalid result. Allowed results: pass, fail, pending"
            )

        return result

    def _validate_moisture(self, moisture_reading):

        if moisture_reading is not None and moisture_reading < 0:
            raise ValueError("Moisture reading cannot be negative")

    # CREATE QUALITY TEST
    def create_quality(self, data: dict, user_id=None):

        data = dict(data)

        required_fields = ("batch_id", "result", "tested_at")

        for field in required_fields:

            if field not in data or data[field] is None:
                raise ValueError(
                    f"{field.replace('_', ' ').title()} is required"
                )

        self._validate_batch(data["batch_id"])

        data["result"] = self._validate_result(data["result"])

        self._validate_moisture(data.get("moisture_reading"))

        try:

            quality = self.repository.create(
                data,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=user_id,
                action="CREATE",
                entity_type="QualityTest",
                entity_id=quality.id,
                new_value=self._quality_snapshot(quality),
                commit=False
            )

            self.db.commit()
            self.db.refresh(quality)

            return quality

        except Exception:
            self.db.rollback()
            raise

    # GET ALL QUALITY TESTS
    def get_all_quality(self):

        return self.repository.get_all()

    # GET QUALITY BY ID
    def get_quality_by_id(self, quality_id):

        quality = self.repository.get_by_id(quality_id)

        if not quality:
            raise LookupError("Quality test not found")

        return quality

    # UPDATE QUALITY TEST
    def update_quality(self, quality_id, data: dict, user_id=None):

        quality = self.get_quality_by_id(quality_id)

        data = dict(data)

        allowed_fields = {
            "moisture_reading",
            "result",
            "tested_at"
        }

        invalid_fields = set(data) - allowed_fields

        if invalid_fields:
            raise ValueError(
                f"Fields cannot be updated: {', '.join(invalid_fields)}"
            )

        if not data:
            return quality

        for field, value in data.items():

            if value is None:
                raise ValueError(
                    f"{field.replace('_', ' ').title()} cannot be empty"
                )

        if "result" in data:
            data["result"] = self._validate_result(data["result"])

        if "moisture_reading" in data:
            self._validate_moisture(data["moisture_reading"])

        old_value = self._quality_snapshot(quality)

        has_changes = any(
            old_value.get(key) != (
                value.isoformat()
                if hasattr(value, "isoformat")
                else value
            )
            for key, value in data.items()
        )

        if not has_changes:
            return quality

        try:

            updated_quality = self.repository.update(
                quality_id,
                data,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=user_id,
                action="UPDATE",
                entity_type="QualityTest",
                entity_id=quality_id,
                old_value=old_value,
                new_value=self._quality_snapshot(updated_quality),
                commit=False
            )

            self.db.commit()
            self.db.refresh(updated_quality)

            return updated_quality

        except Exception:
            self.db.rollback()
            raise

    # DELETE QUALITY TEST
    def delete_quality(self, quality_id, user_id=None):

        try:

            quality = self.get_quality_by_id(quality_id)

            old_value = self._quality_snapshot(quality)

            record_audit(
                db=self.db,
                user_id=user_id,
                action="DELETE",
                entity_type="QualityTest",
                entity_id=quality_id,
                old_value=old_value,
                new_value=None,
                commit=False
            )

            self.repository.delete(
                quality_id,
                commit=False
            )

            self.db.commit()

            return {
                "message": "Quality test deleted successfully"
            }

        except Exception:
            self.db.rollback()
            raise
