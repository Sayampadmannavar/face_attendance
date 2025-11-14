# email_notifier.py
"""
Email notifier using Gmail SMTP.
"""

import smtplib
from email.message import EmailMessage

# --- TEST CREDENTIALS (use env vars in production) ---
SMTP_USER = "sayampadmannavar0@gmail.com"
SMTP_APP_PASSWORD = "szky wbpe zqem gzfg"  # you've provided this for testing
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

def send_attendance_email(to_email: str, name: str, user_id: str, timestamp_str: str):
    subject = "Attendance Recorded"
    body = f"Hello {name},\n\nYour attendance has been recorded.\n\nUser ID: {user_id}\nTime: {timestamp_str}\n\nRegards,\nAttendance System"
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
    # quick test (change address if needed)
    send_attendance_email("someone@example.com", "Test User", "u001", "2025-10-27 12:00:00")
