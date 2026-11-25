
from app.repositories.base_repository import BaseRepository
from app.models.quality import QualityTest


class QualityRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(db, QualityTest)

    def get_by_batch_id(self, batch_id):
        return (
            self.db.query(QualityTest)
            .filter(QualityTest.batch_id == batch_id)
            .all()
        )

    def get_by_result(self, result):
        return (
            self.db.query(QualityTest)
            .filter(QualityTest.result == result)
            .all()
        )
