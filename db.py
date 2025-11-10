"""
db.py — Local SQLite database for Face Attendance System (no XAMPP required)
"""

import sqlite3
from datetime import datetime
import os

DB_PATH = "face_attendance.db"

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()
    # Create users table
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT
                )''')
    # Create attendance table
    c.execute('''CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    time TEXT,
                    status TEXT,
                    FOREIGN KEY(user_id) REFERENCES users(user_id)
                )''')
    conn.commit()
    conn.close()

def add_user(user_id, name, email):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO users (user_id, name, email) VALUES (?, ?, ?)",
              (user_id, name, email))
    conn.commit()
    conn.close()

def get_user_by_userid(user_id):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()
    return dict(row) if row else None

def add_attendance(user_id, status="Present"):
    conn = get_connection()
    c = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("INSERT INTO attendance (user_id, time, status) VALUES (?, ?, ?)",
              (user_id, timestamp, status))
    conn.commit()
    conn.close()

def fetch_attendance():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT a.id, u.name, u.email, a.time, a.status as note
        FROM attendance a
        JOIN users u ON a.user_id = u.user_id
        ORDER BY a.time DESC
    """)
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

# Initialize DB on import
if not os.path.exists(DB_PATH):
    init_db()
