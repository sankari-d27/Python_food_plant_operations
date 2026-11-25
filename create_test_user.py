
import sqlite3
from getpass import getpass

from app.security import hash_password

DATABASE = "food_plant.db"

username = input("Enter production username: ").strip()
email = input("Enter production email: ").strip()
password = getpass("Enter production password: ")

if not username or not email or not password:
    print("All fields are required.")
    raise SystemExit(1)

conn = sqlite3.connect(DATABASE)

try:
    existing = conn.execute(
        "SELECT id FROM users WHERE username = ? OR email = ?",
        (username, email)
    ).fetchone()

    if existing:
        print("Username or email already exists.")
        raise SystemExit(1)

    password_hash = hash_password(password)

    conn.execute(
        """
        INSERT INTO users
        (username, email, password_hash, role, is_active)
        VALUES (?, ?, ?, ?, ?)
        """,
        (username, email, password_hash, "production", 1)
    )

    conn.commit()
    print("Production user created successfully!")

except Exception:
    conn.rollback()
    raise

finally:
    conn.close()
