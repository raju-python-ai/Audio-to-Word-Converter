import sqlite3
from config import DATABASE

def init_db():
    """Create users table if not exists"""
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            mobile TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()


def add_user(username, mobile, email, password):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, mobile, email, password)
        VALUES (?, ?, ?, ?)
    """, (username, mobile, email, password))
    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_user(email, username=None, mobile=None, password=None):
    """
    Update user details for a given email.
    Only updates fields provided (non-None).
    """
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    fields = []
    values = []
    if username:
        fields.append("username = ?")
        values.append(username)
    if mobile:
        fields.append("mobile = ?")
        values.append(mobile)
    if password:
        fields.append("password = ?")
        values.append(password)

    if not fields:
        conn.close()
        return False  # nothing to update

    query = f"UPDATE users SET {', '.join(fields)} WHERE email = ?"
    values.append(email)

    cursor.execute(query, tuple(values))
    conn.commit()
    conn.close()
    return True

def get_user_by_id(user_id):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user


def user_exists(email):
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE email = ?", (email,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists
