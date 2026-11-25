
from app.repositories.user_repository import UserRepository


class UserService:

    def __init__(self, db):
        self.repository = UserRepository(db)

    def create_user(self, data):

        if self.repository.get_by_username(data["username"]):
            raise ValueError("Username already exists")

        if self.repository.get_by_email(data["email"]):
            raise ValueError("Email already exists")

        return self.repository.create(data)

    def get_users(self):
        return self.repository.get_all()
