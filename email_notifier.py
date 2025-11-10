"""
email_notifier.py — Gmail SMTP notifier for Face Attendance System
"""

import smtplib
from email.message import EmailMessage
from datetime import datetime
import os

# --- SMTP CONFIGURATION ---
# For security, set these as environment variables.
# Example (in CMD before running app):
#   set SMTP_USER="your_email@gmail.com"
#   set SMTP_PASS="your_app_password"
SMTP_USER = os.getenv("SMTP_USER", "sayampadmannavar0@gmail.com")
SMTP_APP_PASSWORD = os.getenv("SMTP_PASS", "szky wbpe zqem gzfg")  # fallback for testing

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587  # TLS port


def send_attendance_email(to_email: str, name: str, user_id: str, timestamp_str: str) -> bool:
    """
    Sends an attendance notification email to a registered user.
    Returns True on success, False on failure.
    """
    subject = "Attendance Recorded ✅"
    body = (
        f"Hello {name},\n\n"
        f"Your attendance has been successfully recorded.\n\n"
        f"🆔 User ID: {user_id}\n"
        f"🕒 Time: {timestamp_str}\n\n"
        "Thank you for using the Face Recognition Attendance System.\n"
        "Best regards,\nAttendance System Team"
    )

    msg = EmailMessage()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(SMTP_USER, SMTP_APP_PASSWORD)
            smtp.send_message(msg)

        print(f"[EMAIL SENT] Attendance mail delivered to {to_email}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[ERROR] Authentication failed — check your Gmail App Password.")
        return False
    except Exception as e:
        print(f"[ERROR] Could not send email to {to_email}: {e}")
        return False


if __name__ == "__main__":
    # Quick test — run this file directly to check email setup
    test_email = input("Enter test recipient email: ").strip()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if send_attendance_email(test_email, "Test User", "U001", now_str):
        print("✅ Test email sent successfully.")
    else:
        print("❌ Test email failed.")
