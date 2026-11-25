
from datetime import date
from sqlalchemy.orm import Session

from app.models.batch import Batch
from app.models.production import Production

from app.repositories.production_repository import ProductionRepository
from app.services.audit_helper import record_audit


class ProductionService:

    VALID_SHIFTS = {"Morning", "Afternoon", "Night"}

    def __init__(self, db: Session):

        self.db = db
        self.repository = ProductionRepository(db)

    # PRODUCTION SNAPSHOT
    def _production_snapshot(self, production):

        return {
            "id": production.id,
            "batch_id": production.batch_id,
            "production_date": (
                production.production_date.isoformat()
                if production.production_date else None
            ),
            "input_quantity": production.input_quantity,
            "output_quantity": production.output_quantity,
            "wastage_quantity": production.wastage_quantity,
            "shift": production.shift
        }

    # VALIDATE REQUIRED FIELDS
    def _validate_required_fields(self, data):

        required_fields = (
            "batch_id",
            "production_date",
            "input_quantity",
            "output_quantity",
            "shift"
        )

        for field in required_fields:

            if field not in data or data[field] is None:
                raise ValueError(
                    f"{field.replace('_', ' ').title()} is required"
                )

    # VALIDATE QUANTITIES
    def _validate_quantities(self, data):

        input_quantity = data.get("input_quantity")
        output_quantity = data.get("output_quantity")
        wastage_quantity = data.get("wastage_quantity", 0)

        for field, value in (
            ("input_quantity", input_quantity),
            ("output_quantity", output_quantity),
            ("wastage_quantity", wastage_quantity)
        ):

            if value is not None and value < 0:
                raise ValueError(
                    f"{field.replace('_', ' ').title()} "
                    "cannot be negative"
                )

        if input_quantity is not None and input_quantity <= 0:
            raise ValueError("Input quantity must be greater than zero")

        if (
            input_quantity is not None
            and output_quantity is not None
            and wastage_quantity is not None
            and output_quantity + wastage_quantity > input_quantity
        ):
            raise ValueError(
                "Output quantity plus wastage quantity "
                "cannot exceed input quantity"
            )

    # VALIDATE BATCH
    def _validate_batch(self, batch_id):

        batch = (
            self.db.query(Batch)
            .filter(Batch.id == batch_id)
            .first()
        )

        if not batch:
            raise ValueError("Batch does not exist")

    # VALIDATE SHIFT
    def _validate_shift(self, shift):

        if not isinstance(shift, str):
            raise ValueError("Shift must be text")

        shift = shift.strip()

        if shift not in self.VALID_SHIFTS:
            raise ValueError(
                "Invalid shift. Allowed shifts: "
                "Morning, Afternoon, Night"
            )

        return shift

    # CREATE PRODUCTION
    def create_production(self, data: dict, user_id=None):

        data = dict(data)

        if "wastage_quantity" not in data:
            data["wastage_quantity"] = 0.0

        self._validate_required_fields(data)
        self._validate_quantities(data)

        data["shift"] = self._validate_shift(data["shift"])

        self._validate_batch(data["batch_id"])

        try:

            production = self.repository.create(
                data,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=user_id,
                action="CREATE",
                entity_type="Production",
                entity_id=production.id,
                new_value=self._production_snapshot(production),
                commit=False
            )

            self.db.commit()
            self.db.refresh(production)

            return production

        except Exception:
            self.db.rollback()
            raise

    # GET ALL PRODUCTION RECORDS
    def get_productions(self):

        return self.repository.get_all()

    # GET PRODUCTION BY ID
    def get_production_by_id(self, production_id: int):

        production = self.repository.get_by_id(production_id)

        if not production:
            raise LookupError("Production record not found")

        return production

    # UPDATE PRODUCTION
    def update_production(
        self,
        production_id: int,
        data: dict,
        user_id=None
    ):

        production = self.get_production_by_id(production_id)

        data = dict(data)

        allowed_fields = {
            "production_date",
            "input_quantity",
            "output_quantity",
            "wastage_quantity",
            "shift"
        }

        invalid_fields = set(data.keys()) - allowed_fields

        if invalid_fields:
            raise ValueError(
                f"Fields cannot be updated: {', '.join(invalid_fields)}"
            )

        if not data:
            return production

        current_values = self._production_snapshot(production)

        merged_data = {
            "input_quantity": production.input_quantity,
            "output_quantity": production.output_quantity,
            "wastage_quantity": production.wastage_quantity,
            **data
        }

        for field in data:

            if data[field] is None:
                raise ValueError(
                    f"{field.replace('_', ' ').title()} cannot be empty"
                )

        self._validate_quantities(merged_data)

        if "shift" in data:
            data["shift"] = self._validate_shift(data["shift"])

        has_changes = any(
            current_values.get(key) != (
                value.isoformat()
                if hasattr(value, "isoformat")
                else value
            )
            for key, value in data.items()
        )

        if not has_changes:
            return production

        try:

            updated_production = self.repository.update(
                production_id,
                data,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=user_id,
                action="UPDATE",
                entity_type="Production",
                entity_id=production_id,
                old_value=current_values,
                new_value=self._production_snapshot(updated_production),
                commit=False
            )

            self.db.commit()
            self.db.refresh(updated_production)

            return updated_production

        except Exception:
            self.db.rollback()
            raise

    # DELETE PRODUCTION
    def delete_production(self, production_id: int, user_id=None):

        try:

            production = self.get_production_by_id(production_id)

            old_value = self._production_snapshot(production)

            record_audit(
                db=self.db,
                user_id=user_id,
                action="DELETE",
                entity_type="Production",
                entity_id=production_id,
                old_value=old_value,
                new_value=None,
                commit=False
            )

            self.repository.delete(
                production_id,
                commit=False
            )

            self.db.commit()

            return {
                "message": "Production record deleted successfully"
            }

        except Exception:
            self.db.rollback()
            raise
