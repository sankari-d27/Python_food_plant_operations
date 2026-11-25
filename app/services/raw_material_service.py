
import math

from sqlalchemy.orm import Session

from app.repositories.raw_material_repository import RawMaterialRepository
from app.repositories.supplier_repository import SupplierRepository
from app.services.audit_helper import record_audit


class RawMaterialService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = RawMaterialRepository(db)
        self.supplier_repository = SupplierRepository(db)

    def _raw_material_snapshot(self, material):

        return {
            "id": material.id,
            "material_code": material.material_code,
            "material_name": material.material_name,
            "supplier_id": material.supplier_id,
            "available_quantity": material.available_quantity,
            "unit": material.unit,
            "is_active": material.is_active
        }

    def _validate_required_fields(self, data):

        for field in ("material_code", "material_name", "unit"):

            if field in data:
                value = data[field]

                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"{field.replace('_', ' ').title()} is required"
                    )

    def _validate_quantity(self, data):

        if "available_quantity" not in data:
            return

        quantity = data["available_quantity"]

        if quantity is None:
            return

        if (
            isinstance(quantity, bool)
            or not isinstance(quantity, (int, float))
            or not math.isfinite(quantity)
            or quantity < 0
        ):
            raise ValueError(
                "Available quantity must be a nonnegative number"
            )

    def _validate_supplier(self, supplier_id):

        if supplier_id is None:
            raise ValueError("Supplier ID is required")

        supplier = self.supplier_repository.get_by_id(supplier_id)

        if not supplier:
            raise ValueError("Supplier not found")

        return supplier

    # CREATE RAW MATERIAL
    def create_raw_material(self, data: dict, user_id=None):

        data = dict(data)

        self._validate_required_fields(data)

        if not data.get("material_code"):
            raise ValueError("Material code is required")

        if not data.get("material_name"):
            raise ValueError("Material name is required")

        if not data.get("unit"):
            raise ValueError("Unit is required")

        data["material_code"] = data["material_code"].strip()
        data["material_name"] = data["material_name"].strip()
        data["unit"] = data["unit"].strip()

        self._validate_quantity(data)
        self._validate_supplier(data.get("supplier_id"))

        existing = self.repository.get_by_material_code(
            data["material_code"]
        )

        if existing:
            raise ValueError("Material code already exists")

        try:
            material = self.repository.create(
                data,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=user_id,
                action="CREATE",
                entity_type="RawMaterial",
                entity_id=material.id,
                new_value=self._raw_material_snapshot(material),
                commit=False
            )

            self.db.commit()
            self.db.refresh(material)

            return material

        except Exception:
            self.db.rollback()
            raise

    # GET ALL RAW MATERIALS
    def get_raw_materials(self):
        return self.repository.get_all()

    # GET RAW MATERIAL BY ID
    def get_raw_material_by_id(self, material_id: int):

        material = self.repository.get_by_id(material_id)

        if not material:
            raise LookupError("Raw material not found")

        return material

    # UPDATE RAW MATERIAL
    def update_raw_material(
        self,
        material_id: int,
        data: dict,
        user_id=None
    ):

        material = self.get_raw_material_by_id(material_id)

        data = dict(data)

        self._validate_required_fields(data)
        self._validate_quantity(data)

        if "material_code" in data:

            if data["material_code"] is None:
                raise ValueError("Material code cannot be empty")

            data["material_code"] = data["material_code"].strip()

            existing = self.repository.get_by_material_code(
                data["material_code"]
            )

            if existing and existing.id != material_id:
                raise ValueError("Material code already exists")

        if "material_name" in data:

            if data["material_name"] is None:
                raise ValueError("Material name cannot be empty")

            data["material_name"] = data["material_name"].strip()

        if "unit" in data:

            if data["unit"] is None:
                raise ValueError("Unit cannot be empty")

            data["unit"] = data["unit"].strip()

        if "supplier_id" in data:
            self._validate_supplier(data["supplier_id"])

        old_value = self._raw_material_snapshot(material)

        has_changes = any(
            old_value.get(key) != value
            for key, value in data.items()
        )

        if not has_changes:
            return material

        try:
            updated_material = self.repository.update(
                material_id,
                data,
                commit=False
            )

            new_value = self._raw_material_snapshot(updated_material)

            record_audit(
                db=self.db,
                user_id=user_id,
                action="UPDATE",
                entity_type="RawMaterial",
                entity_id=material_id,
                old_value=old_value,
                new_value=new_value,
                commit=False
            )

            self.db.commit()
            self.db.refresh(updated_material)

            return updated_material

        except Exception:
            self.db.rollback()
            raise

    # DELETE RAW MATERIAL
    def delete_raw_material(self, material_id: int, user_id=None):

        try:
            material = self.get_raw_material_by_id(material_id)

            old_value = self._raw_material_snapshot(material)

            record_audit(
                db=self.db,
                user_id=user_id,
                action="DELETE",
                entity_type="RawMaterial",
                entity_id=material_id,
                old_value=old_value,
                new_value=None,
                commit=False
            )

            self.repository.delete(
                material_id,
                commit=False
            )

            self.db.commit()

            return {
                "message": "Raw material deleted successfully"
            }

        except Exception:
            self.db.rollback()
            raise
