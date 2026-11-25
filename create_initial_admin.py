
from getpass import getpass

from app.database import SessionLocal
from app.models.user import User
from app.security import hash_password


def create_initial_admin():

    db = SessionLocal()

    try:
        print("\n=== CREATE INITIAL ADMINISTRATOR ===")

        username = input("Administrator username: ").strip()
        email = input("Administrator email: ").strip()

        password = input("Administrator password: ")

        if len(password) < 12:
            print("Password must contain at least 12 characters")
            return

        confirm_password = input("Confirm password: ")

        if password != confirm_password:
            print("Passwords do not match")
            return

        existing = db.query(User).filter(
            (User.username == username) |
            (User.email == email)
        ).first()

        if existing:
            print("Username or email already exists")
            return

        admin = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True
        )

        db.add(admin)
        db.commit()

        print("\nAdministrator created successfully!")
        print("Username:", username)
        print("Role: admin")

    except Exception as exc:
        db.rollback()
        print("ERROR:", str(exc))

    finally:
        db.close()


if __name__ == "__main__":
    create_initial_admin()
