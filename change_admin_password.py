
from getpass import getpass

from app.database import SessionLocal
from app.models.user import User
from app.security import hash_password


def change_admin_password():

    db = SessionLocal()

    try:
        username = input("Administrator username: ").strip()

        user = db.query(User).filter(
            User.username == username,
            User.role == "admin"
        ).first()

        if not user:
            print("Administrator not found")
            return

        new_password = getpass("Enter new password: ")

        if len(new_password) < 12:
            print("Password must contain at least 12 characters")
            return

        confirm_password = getpass("Confirm new password: ")

        if new_password != confirm_password:
            print("Passwords do not match")
            return

        user.password_hash = hash_password(new_password)

        db.commit()

        print("\nAdministrator password changed successfully!")

    except Exception as exc:
        db.rollback()
        print("Error:", str(exc))

    finally:
        db.close()


if __name__ == "__main__":
    change_admin_password()
