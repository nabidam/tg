import sqlite3

conn = sqlite3.connect("db.db")

cursor = conn.cursor()

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    phone TEXT,
    bday TEXT,
    bio TEXT,
    is_verified BOOLEAN DEFAULT 0,
    is_bot BOOLEAN DEFAULT 0
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS avatars (
    id INTEGER PRIMARY KEY,
    user_id INTEGERT,
    path TEXT
)
"""
)

conn.commit()
conn.close()

print("Database and users table created successfully.")
