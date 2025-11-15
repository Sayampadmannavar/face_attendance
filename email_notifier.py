# email_notifier.py
"""
Email notifier using SMTP. This module reads SMTP configuration from environment
variables so credentials are not stored in the repo.

Required environment variables:
- SMTP_USER
- SMTP_APP_PASSWORD
- SMTP_SERVER (optional, defaults to smtp.gmail.com)
- SMTP_PORT (optional, defaults to 587)

Usage: set the env vars (or use a `.env` during local dev) and the rest of the
project can call `send_attendance_email(...)`.
"""

import os
import smtplib
from email.message import EmailMessage

SMTP_USER = os.environ.get("SMTP_USER")
SMTP_APP_PASSWORD = os.environ.get("SMTP_APP_PASSWORD")
SMTP_SERVER = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", 587))

def _smtp_config_valid():
    return bool(SMTP_USER and SMTP_APP_PASSWORD)

def send_attendance_email(to_email: str, name: str, user_id: str, timestamp_str: str):
    if not _smtp_config_valid():
        raise RuntimeError("SMTP configuration missing. Set SMTP_USER and SMTP_APP_PASSWORD environment variables.")

    subject = "Attendance Recorded"
    body = (
        f"Hello {name},\n\nYour attendance has been recorded.\n\n"
        f"User ID: {user_id}\nTime: {timestamp_str}\n\nRegards,\nAttendance System"
    )

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        smtp = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        smtp.ehlo()
        smtp.starttls()
        smtp.login(SMTP_USER, SMTP_APP_PASSWORD)
        smtp.send_message(msg)
        smtp.quit()
        print(f"[INFO] Email sent to {to_email}")
        return True
    except Exception as e:
        print("[ERROR] Failed to send email:", e)
        return False

if __name__ == "__main__":
    # simple local test — ensure env vars are configured first
    try:
        send_attendance_email("someone@example.com", "Test User", "u001", "2025-10-27 12:00:00")
    except Exception as e:
        print("SMTP config missing or test failed:", e)
