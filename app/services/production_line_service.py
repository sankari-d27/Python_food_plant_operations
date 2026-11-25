
from sqlalchemy.orm import Session

from app.repositories.production_line_repository import (
    ProductionLineRepository
)
from app.repositories.machine_repository import MachineRepository
from app.services.audit_helper import record_audit


class ProductionLineService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = ProductionLineRepository(db)
        self.machine_repository = MachineRepository(db)

    def _production_line_snapshot(self, line):

        return {
            "id": line.id,
            "line_code": line.line_code,
            "line_name": line.line_name,
            "description": line.description,
            "is_active": line.is_active
        }

    def _validate_required_fields(self, data):

        for field in ("line_code", "line_name"):

            if field in data:
                value = data[field]

                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"{field.replace('_', ' ').title()} is required"
                    )

    # CREATE PRODUCTION LINE
    def create_production_line(self, data: dict, user_id=None):

        data = dict(data)

        self._validate_required_fields(data)

        if not data.get("line_code"):
            raise ValueError("Line code is required")

        if not data.get("line_name"):
            raise ValueError("Line name is required")

        data["line_code"] = data["line_code"].strip()
        data["line_name"] = data["line_name"].strip()

        existing = self.repository.get_by_line_code(
            data["line_code"]
        )

        if existing:
            raise ValueError("Production line code already exists")

        try:
            line = self.repository.create(
                data,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=user_id,
                action="CREATE",
                entity_type="ProductionLine",
                entity_id=line.id,
                new_value=self._production_line_snapshot(line),
                commit=False
            )

            self.db.commit()
            self.db.refresh(line)

            return line

        except Exception:
            self.db.rollback()
            raise

    # GET ALL PRODUCTION LINES
    def get_production_lines(self):
        return self.repository.get_all()

    # GET PRODUCTION LINE BY ID
    def get_production_line_by_id(self, line_id: int):

        line = self.repository.get_by_id(line_id)

        if not line:
            raise LookupError("Production line not found")

        return line

    # UPDATE PRODUCTION LINE
    def update_production_line(
        self,
        line_id: int,
        data: dict,
        user_id=None
    ):

        line = self.get_production_line_by_id(line_id)

        data = dict(data)

        self._validate_required_fields(data)

        if "line_code" in data:

            if data["line_code"] is None:
                raise ValueError("Line code cannot be empty")

            data["line_code"] = data["line_code"].strip()

            existing = self.repository.get_by_line_code(
                data["line_code"]
            )

            if existing and existing.id != line_id:
                raise ValueError(
                    "Production line code already exists"
                )

        if "line_name" in data:

            if data["line_name"] is None:
                raise ValueError("Line name cannot be empty")

            data["line_name"] = data["line_name"].strip()

        old_value = self._production_line_snapshot(line)

        has_changes = any(
            old_value.get(key) != value
            for key, value in data.items()
        )

        if not has_changes:
            return line

        try:
            updated_line = self.repository.update(
                line_id,
                data,
                commit=False
            )

            new_value = self._production_line_snapshot(updated_line)

            record_audit(
                db=self.db,
                user_id=user_id,
                action="UPDATE",
                entity_type="ProductionLine",
                entity_id=line_id,
                old_value=old_value,
                new_value=new_value,
                commit=False
            )

            self.db.commit()
            self.db.refresh(updated_line)

            return updated_line

        except Exception:
            self.db.rollback()
            raise

    # DELETE PRODUCTION LINE
    def delete_production_line(self, line_id: int, user_id=None):

        try:
            line = self.get_production_line_by_id(line_id)

            # Prevent deletion if machines use this production line
            machines = self.machine_repository.get_by_production_line_id(
                line_id
            )

            if machines:
                raise ValueError(
                    "Cannot delete production line because machines "
                    "are assigned to it"
                )

            old_value = self._production_line_snapshot(line)

            record_audit(
                db=self.db,
                user_id=user_id,
                action="DELETE",
                entity_type="ProductionLine",
                entity_id=line_id,
                old_value=old_value,
                new_value=None,
                commit=False
            )

            self.repository.delete(
                line_id,
                commit=False
            )

            self.db.commit()

            return {
                "message": "Production line deleted successfully"
            }

        except Exception:
            self.db.rollback()
            raise
