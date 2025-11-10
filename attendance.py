"""
attendance.py — Handles marking attendance after face recognition.
Uses SQLite (face_attendance.db) and sends email notifications.
"""

import cv2
import numpy as np
import os
from datetime import datetime
from db import add_attendance, get_user_by_userid
from email_notifier import send_attendance_email

# Path to the Haar Cascade classifier
CASCADE_PATH = "haarcascades/haarcascade_frontalface_default.xml"
FACE_RECOGNIZER_PATH = "trainer/trainer.yml"

# Initialize face detector
face_detector = cv2.CascadeClassifier(CASCADE_PATH)

# Initialize face recognizer (LBPH Face Recognizer)
# Ensure OpenCV is installed with contrib modules (opencv-contrib-python)
try:
    recognizer = cv2.face.LBPHFaceRecognizer_create()
except AttributeError:
    raise RuntimeError(
        "❌ OpenCV not compiled with 'face' module.\n"
        "Please install it using:\n"
        "pip install opencv-contrib-python"
    )

# Load trained model if available
if os.path.exists(FACE_RECOGNIZER_PATH):
    recognizer.read(FACE_RECOGNIZER_PATH)
else:
    raise FileNotFoundError("❌ Trainer file not found! Please run train.py first.")


def mark_attendance():
    """
    Starts webcam, recognizes faces, and marks attendance in the database.
    Sends an email notification after successful recognition.
    """
    cam = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    font = cv2.FONT_HERSHEY_SIMPLEX

    print("\n[INFO] Starting face recognition... Press 'q' to quit.\n")

    while True:
        ret, frame = cam.read()
        if not ret:
            print("❌ Camera not detected.")
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_detector.detectMultiScale(gray, 1.2, 5)

        for (x, y, w, h) in faces:
            user_id_pred, confidence = recognizer.predict(gray[y:y+h, x:x+w])
            confidence_percent = round(100 - confidence)

            if confidence_percent > 55:  # confident enough
                # Fetch user info from DB
                user = get_user_by_userid(str(user_id_pred))

                if user:
                    name = user["name"]
                    user_id = user["user_id"]
                    email = user["email"]
                    timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    # Mark attendance in DB
                    add_attendance(user_id)

                    # Draw rectangle & display user info
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, f"{name} ({confidence_percent}%)", (x + 5, y - 5), font, 0.8, (0, 255, 0), 2)

                    # Send email
                    print(f"[INFO] Marked attendance for {name} ({user_id})")
                    send_attendance_email(email, name, user_id, timestamp_str)

                else:
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(frame, "Unknown", (x + 5, y - 5), font, 0.8, (0, 0, 255), 2)

            else:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                cv2.putText(frame, "Uncertain", (x + 5, y - 5), font, 0.8, (0, 0, 255), 2)

        cv2.imshow("Face Attendance System", frame)

        # Exit on pressing 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    print("\n[INFO] Attendance session ended.\n")


if __name__ == "__main__":
    mark_attendance()
