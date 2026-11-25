
from sqlalchemy.orm import Session

from app.repositories.machine_repository import MachineRepository
from app.repositories.base_repository import BaseRepository
from app.models.production_line import ProductionLine
from app.services.audit_helper import record_audit


class MachineService:

    VALID_STATUSES = {
        "available",
        "running",
        "maintenance",
        "breakdown",
        "inactive"
    }

    def __init__(self, db: Session):
        self.db = db
        self.repository = MachineRepository(db)
        self.production_line_repository = BaseRepository(
            db,
            ProductionLine
        )

    def _machine_snapshot(self, machine):

        return {
            "id": machine.id,
            "machine_code": machine.machine_code,
            "machine_name": machine.machine_name,
            "production_line_id": machine.production_line_id,
            "machine_status": machine.machine_status,
            "is_active": machine.is_active
        }

    def _validate_required_fields(self, data):

        for field in ("machine_code", "machine_name"):

            if field in data:
                value = data[field]

                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"{field.replace('_', ' ').title()} is required"
                    )

    def _validate_production_line(self, production_line_id):

        if production_line_id is None:
            raise ValueError("Production line ID is required")

        production_line = (
            self.production_line_repository.get_by_id(
                production_line_id
            )
        )

        if not production_line:
            raise ValueError("Production line not found")

        return production_line

    def _validate_status(self, data):

        if "machine_status" not in data:
            return

        status = data["machine_status"]

        if not isinstance(status, str) or not status.strip():
            raise ValueError("Machine status is required")

        data["machine_status"] = status.strip().lower()

        if data["machine_status"] not in self.VALID_STATUSES:
            raise ValueError("Invalid machine status")

    # CREATE MACHINE
    def create_machine(self, data: dict, user_id=None):

        data = dict(data)

        self._validate_required_fields(data)

        if not data.get("machine_code"):
            raise ValueError("Machine code is required")

        if not data.get("machine_name"):
            raise ValueError("Machine name is required")

        data["machine_code"] = data["machine_code"].strip()
        data["machine_name"] = data["machine_name"].strip()

        if "machine_status" not in data:
            data["machine_status"] = "available"

        self._validate_status(data)

        self._validate_production_line(
            data.get("production_line_id")
        )

        existing = self.repository.get_by_machine_code(
            data["machine_code"]
        )

        if existing:
            raise ValueError("Machine code already exists")

        try:
            machine = self.repository.create(
                data,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=user_id,
                action="CREATE",
                entity_type="Machine",
                entity_id=machine.id,
                new_value=self._machine_snapshot(machine),
                commit=False
            )

            self.db.commit()
            self.db.refresh(machine)

            return machine

        except Exception:
            self.db.rollback()
            raise

    # GET ALL MACHINES
    def get_machines(self):
        return self.repository.get_all()

    # GET MACHINE BY ID
    def get_machine_by_id(self, machine_id: int):

        machine = self.repository.get_by_id(machine_id)

        if not machine:
            raise LookupError("Machine not found")

        return machine

    # UPDATE MACHINE
    def update_machine(
        self,
        machine_id: int,
        data: dict,
        user_id=None
    ):

        machine = self.get_machine_by_id(machine_id)

        data = dict(data)

        self._validate_required_fields(data)
        self._validate_status(data)

        if "machine_code" in data:

            if data["machine_code"] is None:
                raise ValueError("Machine code cannot be empty")

            data["machine_code"] = data["machine_code"].strip()

            existing = self.repository.get_by_machine_code(
                data["machine_code"]
            )

            if existing and existing.id != machine_id:
                raise ValueError("Machine code already exists")

        if "machine_name" in data:

            if data["machine_name"] is None:
                raise ValueError("Machine name cannot be empty")

            data["machine_name"] = data["machine_name"].strip()

        if "production_line_id" in data:
            self._validate_production_line(
                data["production_line_id"]
            )

        old_value = self._machine_snapshot(machine)

        has_changes = any(
            old_value.get(key) != value
            for key, value in data.items()
        )

        if not has_changes:
            return machine

        try:
            updated_machine = self.repository.update(
                machine_id,
                data,
                commit=False
            )

            new_value = self._machine_snapshot(updated_machine)

            record_audit(
                db=self.db,
                user_id=user_id,
                action="UPDATE",
                entity_type="Machine",
                entity_id=machine_id,
                old_value=old_value,
                new_value=new_value,
                commit=False
            )

            self.db.commit()
            self.db.refresh(updated_machine)

            return updated_machine

        except Exception:
            self.db.rollback()
            raise

    # DELETE MACHINE
    def delete_machine(self, machine_id: int, user_id=None):

        try:
            machine = self.get_machine_by_id(machine_id)

            old_value = self._machine_snapshot(machine)

            record_audit(
                db=self.db,
                user_id=user_id,
                action="DELETE",
                entity_type="Machine",
                entity_id=machine_id,
                old_value=old_value,
                new_value=None,
                commit=False
            )

            self.repository.delete(
                machine_id,
                commit=False
            )

            self.db.commit()

            return {
                "message": "Machine deleted successfully"
            }

        except Exception:
            self.db.rollback()
            raise
