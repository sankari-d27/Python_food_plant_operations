
from app.repositories.base_repository import BaseRepository
from app.models.machine import Machine


class MachineRepository(BaseRepository):

    def __init__(self, db):
        super().__init__(db, Machine)

    def get_by_machine_code(self, machine_code):
        return (
            self.db.query(Machine)
            .filter(
                Machine.machine_code == machine_code
            )
            .first()
        )

    def get_by_production_line_id(self, production_line_id):
        return (
            self.db.query(Machine)
            .filter(
                Machine.production_line_id == production_line_id
            )
            .all()
        )

    def get_by_status(self, machine_status):
        return (
            self.db.query(Machine)
            .filter(
                Machine.machine_status == machine_status
            )
            .all()
        )
