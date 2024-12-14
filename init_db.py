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

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    date TEXT,
    edit_date TEXT,
    message TEXT,
    raw_text TEXT,
    is_reply BOOLEAN,
    reply_to INTEGER,
    topic_id INTEGER,
    sender_id INTEGER,
    is_sticker BOOLEAN,
    sticker_emoji TEXT
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS reactions (
    user_id INTEGER,
    msg_id INTEGER,
    emoticon TEXT,
    PRIMARY KEY (user_id, msg_id)
)
"""
)

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS topics (
    id INTEGER PRIMARY KEY,
    title TEXT
)
"""
)

# TODO: add msg_id to files

cursor.execute(
    """
CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY,
    ext TEXT,
    height INTEGER,
    width INTEGER,
    mime_type TEXT,
    size INTEGER,
    path TEXT
)
"""
)

conn.commit()
conn.close()

print("Database and tables created successfully.")
