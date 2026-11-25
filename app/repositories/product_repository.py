
from app.repositories.base_repository import BaseRepository
from app.models.product import Product


class ProductRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(db, Product)

    def get_by_product_code(self, product_code):
        return (
            self.db.query(Product)
            .filter(Product.product_code == product_code)
            .first()
        )
