# db.py
"""
Database helper for Face Recognition Attendance System.
Uses mysql-connector-python.
"""

import mysql.connector
from mysql.connector import Error
from datetime import datetime

# Update these for your local MySQL/XAMPP install
DB_CONFIG = {
    "host": "localhost",
    "port": 3306,
    "user": "root",
    "password": "",    # XAMPP default is blank for root
    "database": "face_attendance"
}

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print("DB connection error:", e)
        raise

def init_db():
    """Create database and required tables if they don't exist."""
    tmp_conf = DB_CONFIG.copy()
    tmp_conf.pop("database")
    conn = mysql.connector.connect(**tmp_conf)
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

def add_user(user_id: str, name: str, email: str):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (user_id, name, email, registered_on)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE name=%s, email=%s
    """, (user_id, name, email, datetime.now(), name, email))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_by_userid(user_id: str):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE user_id=%s", (user_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def get_user_by_id_numeric(id_numeric: int):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id=%s", (id_numeric,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    return row

def add_attendance(user_id: str, status="Present"):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO attendance (user_id, login_time, status) VALUES (%s, %s, %s)",
                   (user_id, datetime.now(), status))
    conn.commit()
    cursor.close()
    conn.close()

def fetch_attendance(limit=100):
    conn = get_connection()
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

if __name__ == "__main__":
    init_db()
    print("DB initialized.")
