# db.py
"""
Database helper for Face Recognition Attendance System.
Uses mysql-connector-python.
"""

from datetime import datetime
import os

# Try to use MySQL if available; otherwise fall back to SQLite for local/dev runs.
USE_SQLITE = os.environ.get("DB_USE_SQLITE", "false").lower() in ("1", "true", "yes")
SQLITE_FILE = os.environ.get("DB_SQLITE_FILE", "face_attendance.sqlite3")

DB_CONFIG = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", 3306)),
    "user": os.environ.get("DB_USER", "root"),
    "password": os.environ.get("DB_PASSWORD", ""),
    "database": os.environ.get("DB_DATABASE", "face_attendance")
}

# Lazy import of mysql.connector so the module can still be used without it.
mysql = None
try:
    if not USE_SQLITE:
        import mysql.connector as mysql_connector
        from mysql.connector import Error as MySQLError
        mysql = mysql_connector
except Exception:
    mysql = None

import sqlite3


def _using_mysql_available():
    if USE_SQLITE:
        return False
    if mysql is None:
        return False
    # Try a quick connection test
    try:
        conn = mysql.connect(**DB_CONFIG)
        conn.close()
        return True
    except Exception:
        return False


def get_connection():
    """Return a DB connection. Use MySQL when available; otherwise use SQLite."""
    if _using_mysql_available():
        return mysql.connect(**DB_CONFIG)
    # SQLite fallback
    conn = sqlite3.connect(SQLITE_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create tables for either MySQL or SQLite."""
    if _using_mysql_available():
        tmp_conf = DB_CONFIG.copy()
        tmp_conf.pop("database")
        conn = mysql.connect(**tmp_conf)
        cursor = conn.cursor()
        cursor.execute("CREATE DATABASE IF NOT EXISTS {}".format(DB_CONFIG["database"]))
        conn.commit()
        cursor.close()
        conn.close()

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            registered_on DATETIME NOT NULL
        )""")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id VARCHAR(50) NOT NULL,
            login_time DATETIME NOT NULL,
            status VARCHAR(50)
        )""")
        conn.commit()
        cursor.close()
        conn.close()
        return

    # SQLite path
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        registered_on TEXT NOT NULL
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attendance (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        login_time TEXT NOT NULL,
        status TEXT
    )""")
    conn.commit()
    cursor.close()
    conn.close()


def add_user(user_id: str, name: str, email: str):
    conn = get_connection()
    cursor = conn.cursor()
    if _using_mysql_available():
        cursor.execute("""
            INSERT INTO users (user_id, name, email, registered_on)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE name=%s, email=%s
        """, (user_id, name, email, datetime.now(), name, email))
    else:
        # SQLite upsert
        cursor.execute("""
            INSERT INTO users (user_id, name, email, registered_on)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET name=excluded.name, email=excluded.email
        """, (user_id, name, email, datetime.now()))
    conn.commit()
    cursor.close()
    conn.close()


def _row_to_dict(row):
    if row is None:
        return None
    try:
        return dict(row)
    except Exception:
        return row


def get_user_by_userid(user_id: str):
    conn = get_connection()
    cursor = conn.cursor()
    if _using_mysql_available():
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    else:
        cursor.execute("SELECT * FROM users WHERE user_id=?", (user_id,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return _row_to_dict(row)


def get_user_by_email(email: str):
    """Return a user row by email or None. Works for both MySQL and SQLite."""
    conn = get_connection()
    cursor = conn.cursor()
    if _using_mysql_available():
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    else:
        cursor.execute("SELECT * FROM users WHERE email=?", (email,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return _row_to_dict(row)


def get_user_by_id_numeric(id_numeric: int):
    conn = get_connection()
    cursor = conn.cursor()
    if _using_mysql_available():
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM users WHERE id=%s", (id_numeric,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return row
    else:
        cursor.execute("SELECT * FROM users WHERE id=?", (id_numeric,))
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        return _row_to_dict(row)


def add_attendance(user_id: str, status="Present"):
    conn = get_connection()
    cursor = conn.cursor()
    if _using_mysql_available():
        cursor.execute("INSERT INTO attendance (user_id, login_time, status) VALUES (%s, %s, %s)",
                       (user_id, datetime.now(), status))
    else:
        cursor.execute("INSERT INTO attendance (user_id, login_time, status) VALUES (?, ?, ?)",
                       (user_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), status))
    conn.commit()
    cursor.close()
    conn.close()


def fetch_attendance(limit=100):
    conn = get_connection()
    cursor = conn.cursor()
    if _using_mysql_available():
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.id, a.user_id, u.name, u.email, a.login_time, a.status
            FROM attendance a
            LEFT JOIN users u ON u.user_id = a.user_id
            ORDER BY a.login_time DESC
            LIMIT %s
        """, (limit,))
        rows = cursor.fetchall()
        cursor.close()
        conn.close()
        return rows
    else:
        cursor.execute("""
            SELECT a.id, a.user_id, u.name, u.email, a.login_time, a.status
            FROM attendance a
            LEFT JOIN users u ON u.user_id = a.user_id
            ORDER BY a.login_time DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        # convert sqlite3.Row to dicts
        result = [dict(r) for r in rows]
        cursor.close()
        conn.close()
        return result


if __name__ == "__main__":
    init_db()
    print("DB initialized.")
