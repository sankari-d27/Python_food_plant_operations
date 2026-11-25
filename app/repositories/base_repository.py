
from sqlalchemy.orm import Session


class BaseRepository:

    def __init__(self, db: Session, model):
        self.db = db
        self.model = model

    def create(self, data, commit=True):
        record = self.model(**data)

        self.db.add(record)
        self.db.flush()
        self.db.refresh(record)

        if commit:
            self.db.commit()

        return record

    def get_by_id(self, record_id):
        return (
            self.db.query(self.model)
            .filter(self.model.id == record_id)
            .first()
        )

    def get_all(self):
        return self.db.query(self.model).all()

    def update(self, record_id, data, commit=True):

        record = self.get_by_id(record_id)

        if not record:
            return None

        for key, value in data.items():
            if hasattr(record, key):
                setattr(record, key, value)

        self.db.flush()
        self.db.refresh(record)

        if commit:
            self.db.commit()

        return record

    def delete(self, record_id, commit=True):

        record = self.get_by_id(record_id)

        if not record:
            return False

        self.db.delete(record)
        self.db.flush()

        if commit:
            self.db.commit()

        return True
