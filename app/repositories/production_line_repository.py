
from app.repositories.base_repository import BaseRepository
from app.models.production_line import ProductionLine


class ProductionLineRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(db, ProductionLine)

    def get_by_line_code(self, line_code):
        return (
            self.db.query(ProductionLine)
            .filter(
                ProductionLine.line_code == line_code
            )
            .first()
        )

    def get_by_line_name(self, line_name):
        return (
            self.db.query(ProductionLine)
            .filter(
                ProductionLine.line_name == line_name
            )
            .first()
        )
