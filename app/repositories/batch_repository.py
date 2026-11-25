
from app.repositories.base_repository import BaseRepository
from app.models.batch import Batch


class BatchRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(db, Batch)

    def get_by_batch_number(self, batch_number):
        return (
            self.db.query(Batch)
            .filter(Batch.batch_number == batch_number)
            .first()
        )

    def get_by_status(self, status):
        return (
            self.db.query(Batch)
            .filter(Batch.status == status)
            .all()
        )

    def get_by_product_id(self, product_id):
        return (
            self.db.query(Batch)
            .filter(Batch.product_id == product_id)
            .all()
        )

    def get_by_production_line_id(self, production_line_id):
        return (
            self.db.query(Batch)
            .filter(
                Batch.production_line_id == production_line_id
            )
            .all()
        )
