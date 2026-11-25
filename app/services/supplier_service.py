
from sqlalchemy.orm import Session

from app.repositories.supplier_repository import SupplierRepository
from app.services.audit_helper import record_audit


class SupplierService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = SupplierRepository(db)

    def _supplier_snapshot(self, supplier):
        return {
            "id": supplier.id,
            "supplier_name": supplier.supplier_name,
            "contact_person": supplier.contact_person,
            "phone": supplier.phone,
            "email": supplier.email,
            "address": supplier.address,
            "is_active": supplier.is_active
        }

    def create_supplier(self, data: dict, user_id=None):

        try:
            supplier_name = data.get("supplier_name")

            if not supplier_name or not supplier_name.strip():
                raise ValueError("Supplier name is required")

            data["supplier_name"] = supplier_name.strip()

            existing = self.repository.get_by_name(
                data["supplier_name"]
            )

            if existing:
                raise ValueError("Supplier name already exists")

            supplier = self.repository.create(
                data,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=user_id,
                action="CREATE",
                entity_type="Supplier",
                entity_id=supplier.id,
                new_value=self._supplier_snapshot(supplier),
                commit=False
            )

            self.db.commit()
            self.db.refresh(supplier)

            return supplier

        except Exception:
            self.db.rollback()
            raise

    def get_suppliers(self):
        return self.repository.get_all()

    def get_supplier_by_id(self, supplier_id: int):

        supplier = self.repository.get_by_id(supplier_id)

        if not supplier:
            raise LookupError("Supplier not found")

        return supplier

    
    def update_supplier(
        self,
        supplier_id: int,
        data: dict,
        user_id=None
    ):

        try:
            supplier = self.get_supplier_by_id(supplier_id)

            if "supplier_name" in data:
                name = data["supplier_name"]

                if name is None or not name.strip():
                    raise ValueError("Supplier name is required")

                data["supplier_name"] = name.strip()

                existing = self.repository.get_by_name(
                    data["supplier_name"]
                )

                if existing and existing.id != supplier_id:
                    raise ValueError("Supplier name already exists")

            old_value = self._supplier_snapshot(supplier)

            # Check whether any actual field value has changed
            has_changes = any(
                old_value.get(key) != value
                for key, value in data.items()
            )

            # Return without creating an unnecessary audit record
            if not has_changes:
                return supplier

            updated_supplier = self.repository.update(
                supplier_id,
                data,
                commit=False
            )

            new_value = self._supplier_snapshot(updated_supplier)

            record_audit(
                db=self.db,
                user_id=user_id,
                action="UPDATE",
                entity_type="Supplier",
                entity_id=supplier_id,
                old_value=old_value,
                new_value=new_value,
                commit=False
            )

            self.db.commit()
            self.db.refresh(updated_supplier)

            return updated_supplier

        except Exception:
            self.db.rollback()
            raise

    def delete_supplier(self, supplier_id: int, user_id=None):

        try:
            supplier = self.get_supplier_by_id(supplier_id)

            old_value = self._supplier_snapshot(supplier)

            record_audit(
                db=self.db,
                user_id=user_id,
                action="DELETE",
                entity_type="Supplier",
                entity_id=supplier_id,
                old_value=old_value,
                new_value=None,
                commit=False
            )

            self.repository.delete(
                supplier_id,
                commit=False
            )

            self.db.commit()

            return {
                "message": "Supplier deleted successfully"
            }

        except Exception:
            self.db.rollback()
            raise
