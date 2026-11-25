
from app.repositories.base_repository import BaseRepository
from app.models.supplier import Supplier


class SupplierRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(db, Supplier)

    def get_by_name(self, supplier_name):
        return (
            self.db.query(Supplier)
            .filter(
                Supplier.supplier_name == supplier_name
            )
            .first()
        )
