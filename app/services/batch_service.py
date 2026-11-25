
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.production_line import ProductionLine
from app.models.user import User
from app.models.production import Production
from app.models.quality import QualityTest
from app.models.approval import Approval

from app.repositories.batch_repository import BatchRepository
from app.services.audit_helper import record_audit


class BatchService:

    def __init__(self, db: Session):

        self.db = db
        self.repository = BatchRepository(db)

    # BATCH SNAPSHOT
    def _batch_snapshot(self, batch):

        return {
            "id": batch.id,
            "batch_number": batch.batch_number,
            "product_id": batch.product_id,
            "production_line_id": batch.production_line_id,
            "created_by": batch.created_by,
            "production_date": (
                batch.production_date.isoformat()
                if batch.production_date else None
            ),
            "input_quantity": batch.input_quantity,
            "output_quantity": batch.output_quantity,
            "status": batch.status
        }

    # VALIDATE REQUIRED FIELDS
    def _validate_required_fields(self, data):

        required_fields = (
            "batch_number",
            "product_id",
            "production_line_id",
            "created_by",
            "production_date",
            "input_quantity",
            "output_quantity"
        )

        for field in required_fields:

            if field not in data or data[field] is None:
                raise ValueError(
                    f"{field.replace('_', ' ').title()} is required"
                )

    # VALIDATE QUANTITIES
    def _validate_quantities(self, data):

        for field in ("input_quantity", "output_quantity"):

            if field in data:

                value = data[field]

                if value is None or value < 0:
                    raise ValueError(
                        f"{field.replace('_', ' ').title()} "
                        "cannot be negative"
                    )

    # VALIDATE FOREIGN KEYS
    def _validate_references(self, data):

        if "product_id" in data:

            product = (
                self.db.query(Product)
                .filter(Product.id == data["product_id"])
                .first()
            )

            if not product:
                raise ValueError("Product does not exist")

        if "production_line_id" in data:

            line = (
                self.db.query(ProductionLine)
                .filter(
                    ProductionLine.id == data["production_line_id"]
                )
                .first()
            )

            if not line:
                raise ValueError("Production line does not exist")

        if "created_by" in data:

            user = (
                self.db.query(User)
                .filter(User.id == data["created_by"])
                .first()
            )

            if not user:
                raise ValueError("User does not exist")

    # CREATE BATCH
    def create_batch(self, data: dict, user_id=None):

        data = dict(data)

        self._validate_required_fields(data)
        self._validate_quantities(data)

        if not isinstance(data["batch_number"], str):
            raise ValueError("Batch number must be text")

        data["batch_number"] = data["batch_number"].strip()

        if not data["batch_number"]:
            raise ValueError("Batch number is required")

        if len(data["batch_number"]) > 50:
            raise ValueError("Batch number cannot exceed 50 characters")

        if "status" in data and data["status"] is not None:
            data["status"] = data["status"].strip()

            if not data["status"]:
                raise ValueError("Batch status cannot be empty")

            if len(data["status"]) > 30:
                raise ValueError("Batch status cannot exceed 30 characters")

        self._validate_references(data)

        try:

            batch = self.repository.create(
                data,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=user_id,
                action="CREATE",
                entity_type="Batch",
                entity_id=batch.id,
                new_value=self._batch_snapshot(batch),
                commit=False
            )

            self.db.commit()
            self.db.refresh(batch)

            return batch

        except Exception:
            self.db.rollback()
            raise

    # GET ALL BATCHES
    def get_batches(self):

        return self.repository.get_all()

    # GET BATCH BY ID
    def get_batch_by_id(self, batch_id: int):

        batch = self.repository.get_by_id(batch_id)

        if not batch:
            raise LookupError("Batch not found")

        return batch

    # UPDATE BATCH
    def update_batch(
        self,
        batch_id: int,
        data: dict,
        user_id=None
    ):

        batch = self.get_batch_by_id(batch_id)

        data = dict(data)

        allowed_fields = {
            "batch_number",
            "product_id",
            "production_line_id",
            "production_date",
            "input_quantity",
            "output_quantity",
            "status"
        }

        invalid_fields = set(data.keys()) - allowed_fields

        if invalid_fields:
            raise ValueError(
                f"Fields cannot be updated: {', '.join(invalid_fields)}"
            )

        if "batch_number" in data:

            if data["batch_number"] is None:
                raise ValueError("Batch number cannot be empty")

            if not isinstance(data["batch_number"], str):
                raise ValueError("Batch number must be text")

            data["batch_number"] = data["batch_number"].strip()

            if not data["batch_number"]:
                raise ValueError("Batch number cannot be empty")

            if len(data["batch_number"]) > 50:
                raise ValueError(
                    "Batch number cannot exceed 50 characters"
                )

        for field in (
            "product_id",
            "production_line_id",
            "production_date",
            "input_quantity",
            "output_quantity"
        ):

            if field in data and data[field] is None:
                raise ValueError(
                    f"{field.replace('_', ' ').title()} cannot be empty"
                )

        if "status" in data and data["status"] is not None:

            if not isinstance(data["status"], str):
                raise ValueError("Batch status must be text")

            data["status"] = data["status"].strip()

            if not data["status"]:
                raise ValueError("Batch status cannot be empty")

            if len(data["status"]) > 30:
                raise ValueError(
                    "Batch status cannot exceed 30 characters"
                )

        self._validate_quantities(data)
        self._validate_references(data)

        old_value = self._batch_snapshot(batch)

        has_changes = any(
            old_value.get(key) != (
                value.isoformat()
                if hasattr(value, "isoformat")
                else value
            )
            for key, value in data.items()
        )

        if not has_changes:
            return batch

        try:

            updated_batch = self.repository.update(
                batch_id,
                data,
                commit=False
            )

            new_value = self._batch_snapshot(updated_batch)

            record_audit(
                db=self.db,
                user_id=user_id,
                action="UPDATE",
                entity_type="Batch",
                entity_id=batch_id,
                old_value=old_value,
                new_value=new_value,
                commit=False
            )

            self.db.commit()
            self.db.refresh(updated_batch)

            return updated_batch

        except Exception:
            self.db.rollback()
            raise

    # CHECK BATCH DEPENDENCIES
    def _check_batch_dependencies(self, batch_id):

        production_exists = (
            self.db.query(Production)
            .filter(Production.batch_id == batch_id)
            .first()
        )

        if production_exists:
            raise ValueError(
                "Cannot delete batch because production records "
                "are associated with it"
            )

        quality_exists = (
            self.db.query(QualityTest)
            .filter(QualityTest.batch_id == batch_id)
            .first()
        )

        if quality_exists:
            raise ValueError(
                "Cannot delete batch because quality test records "
                "are associated with it"
            )

        approval_exists = (
            self.db.query(Approval)
            .filter(Approval.batch_id == batch_id)
            .first()
        )

        if approval_exists:
            raise ValueError(
                "Cannot delete batch because approval records "
                "are associated with it"
            )

    # DELETE BATCH
    def delete_batch(self, batch_id: int, user_id=None):

        try:

            batch = self.get_batch_by_id(batch_id)

            self._check_batch_dependencies(batch_id)

            old_value = self._batch_snapshot(batch)

            record_audit(
                db=self.db,
                user_id=user_id,
                action="DELETE",
                entity_type="Batch",
                entity_id=batch_id,
                old_value=old_value,
                new_value=None,
                commit=False
            )

            self.repository.delete(
                batch_id,
                commit=False
            )

            self.db.commit()

            return {
                "message": "Batch deleted successfully"
            }

        except Exception:
            self.db.rollback()
            raise
