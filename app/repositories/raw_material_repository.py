
from app.repositories.base_repository import BaseRepository
from app.models.raw_material import RawMaterial


class RawMaterialRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(db, RawMaterial)

    def get_by_material_code(self, material_code):
        return (
            self.db.query(RawMaterial)
            .filter(
                RawMaterial.material_code == material_code
            )
            .first()
        )

    def get_by_supplier_id(self, supplier_id):
        return (
            self.db.query(RawMaterial)
            .filter(
                RawMaterial.supplier_id == supplier_id
            )
            .all()
        )
