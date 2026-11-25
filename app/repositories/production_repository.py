from app.repositories.base_repository import BaseRepository
from app.models.production import Production


class ProductionRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(db, Production)

    def get_by_batch_id(self, batch_id):
        return (
            self.db.query(Production)
            .filter(Production.batch_id == batch_id)
            .all()
        )

    def get_by_production_date(self, production_date):
        return (
            self.db.query(Production)
            .filter(
                Production.production_date == production_date
            )
            .all()
        )

    def get_by_shift(self, shift):
        return (
            self.db.query(Production)
            .filter(Production.shift == shift)
            .all()
        )