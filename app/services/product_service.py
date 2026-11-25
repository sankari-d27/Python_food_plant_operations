
from app.repositories.product_repository import ProductRepository
from app.services.audit_helper import record_audit


class ProductService:

    def __init__(self, db, current_user=None):
        self.db = db
        self.repository = ProductRepository(db)
        self.current_user = current_user

    def _get_user_id(self):
        return getattr(self.current_user, "id", None)

    def _validate_required_fields(self, data):

        if "product_name" in data:
            if not isinstance(data["product_name"], str) or not data["product_name"].strip():
                raise ValueError("Product name is required")

        if "product_code" in data:
            if not isinstance(data["product_code"], str) or not data["product_code"].strip():
                raise ValueError("Product code is required")

    def _get_product_data(self, product):

        return {
            "id": product.id,
            "product_code": product.product_code,
            "product_name": product.product_name,
            "description": product.description,
            "unit": product.unit,
            "is_active": product.is_active
        }

    # CREATE PRODUCT
    def create_product(self, data):

        data = dict(data)

        self._validate_required_fields(data)

        if not data.get("product_code"):
            raise ValueError("Product code is required")

        data["product_code"] = data["product_code"].strip()
        data["product_name"] = data["product_name"].strip()

        existing = self.repository.get_by_product_code(
            data["product_code"]
        )

        if existing:
            raise ValueError("Product code already exists")

        try:
            product = self.repository.create(
                data,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=self._get_user_id(),
                action="CREATE",
                entity_type="Product",
                entity_id=product.id,
                new_value=self._get_product_data(product),
                commit=False
            )

            self.db.commit()
            self.db.refresh(product)

            return product

        except Exception:
            self.db.rollback()
            raise

    # GET ALL PRODUCTS
    def get_products(self):
        return self.repository.get_all()

    # GET PRODUCT BY ID
    def get_product_by_id(self, product_id):

        product = self.repository.get_by_id(product_id)

        if not product:
            raise ValueError("Product not found")

        return product

    # UPDATE PRODUCT
    def update_product(self, product_id, data):

        product = self.get_product_by_id(product_id)

        data = dict(data)

        self._validate_required_fields(data)

        if "product_code" in data and data["product_code"] is not None:
            data["product_code"] = data["product_code"].strip()

            existing = self.repository.get_by_product_code(
                data["product_code"]
            )

            if existing and existing.id != product_id:
                raise ValueError("Product code already exists")

        if "product_name" in data and data["product_name"] is not None:
            data["product_name"] = data["product_name"].strip()

        if "product_code" in data and data["product_code"] is None:
            raise ValueError("Product code cannot be empty")

        if "product_name" in data and data["product_name"] is None:
            raise ValueError("Product name cannot be empty")

        old_value = self._get_product_data(product)

        try:
            updated_product = self.repository.update(
                product_id,
                data,
                commit=False
            )

            new_value = self._get_product_data(updated_product)

            record_audit(
                db=self.db,
                user_id=self._get_user_id(),
                action="UPDATE",
                entity_type="Product",
                entity_id=updated_product.id,
                old_value=old_value,
                new_value=new_value,
                commit=False
            )

            self.db.commit()
            self.db.refresh(updated_product)

            return updated_product

        except Exception:
            self.db.rollback()
            raise

    # DELETE PRODUCT
    def delete_product(self, product_id):

        product = self.get_product_by_id(product_id)

        old_value = self._get_product_data(product)

        try:
            self.repository.delete(
                product_id,
                commit=False
            )

            record_audit(
                db=self.db,
                user_id=self._get_user_id(),
                action="DELETE",
                entity_type="Product",
                entity_id=product_id,
                old_value=old_value,
                new_value=None,
                commit=False
            )

            self.db.commit()

            return {
                "message": "Product deleted successfully"
            }

        except Exception:
            self.db.rollback()
            raise
