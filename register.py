"""
Register new user: capture face images, check duplicates, and save to dataset.
Optimized with lazy OpenCV loading for faster imports.
"""

import os
import numpy as np
from db import add_user, get_user_by_email
from datetime import datetime

# Lazy-load OpenCV to speed up module import
_cv2 = None

def _get_cv2():
    """Import cv2 only when first needed."""
    global _cv2
    if _cv2 is None:
        import cv2
        _cv2 = cv2
    return _cv2

CASCADE_PATH = os.path.join("haarcascades", "haarcascade_frontalface_default.xml")
DATASET_DIR = "dataset"
TRAINER_DIR = "trainer"
TRAINER_FILE = os.path.join(TRAINER_DIR, "trainer.yml")


def ensure_dirs():
    os.makedirs(DATASET_DIR, exist_ok=True)
    os.makedirs(TRAINER_DIR, exist_ok=True)
    if not os.path.exists(CASCADE_PATH):
        raise FileNotFoundError(f"Haarcascade not found at {CASCADE_PATH}. Download from OpenCV.")


def check_duplicate_email(email):
    """Check if email already exists in DB."""
    user = get_user_by_email(email)
    return user is not None


def check_duplicate_face(face_roi):
    """Check if this face already exists using the trained model."""
    if not os.path.exists(TRAINER_FILE):
        return False  # No trained data yet
    cv2 = _get_cv2()
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(TRAINER_FILE)
    label, confidence = recognizer.predict(face_roi)
    # Lower confidence = more similar (0 = identical)
    return confidence < 70  # Adjust threshold if needed


def register_user(user_id: str, name: str, email: str, samples=30):
    """
    Capture 'samples' images of the user's face via webcam.
    Prevent duplicate faces or emails.
    """
    ensure_dirs()

    # Check duplicate email
    if check_duplicate_email(email):
        raise ValueError(f"This email '{email}' is already registered!")

    # Initialize face detection
    cv2 = _get_cv2()
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        raise RuntimeError("Could not open webcam.")

    print(f"[INFO] Starting capture for {name} ({user_id}). Press 'q' to quit early.")
    count = 0
    duplicate_detected = False

    # Capture loop
    while True:
        ret, img = cam.read()
        if not ret:
            print("[ERROR] Camera read failed.")
            break
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)

        for (x, y, w, h) in faces:
            face_roi = gray[y:y+h, x:x+w]

            # Check if this face already exists
            if check_duplicate_face(face_roi):
                print("This face already exists in the system! Registration aborted.")
                duplicate_detected = True
                break

            count += 1
            filepath = os.path.join(DATASET_DIR, f"{user_id}_{count}.jpg")
            cv2.imwrite(filepath, face_roi)
            cv2.rectangle(img, (x, y), (x+w, y+h), (255, 0, 0), 2)
            cv2.putText(img, f"{count}/{samples}", (x, y-10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 0, 0), 2)

        cv2.imshow("Register - Press q to Quit", img)
        k = cv2.waitKey(1) & 0xFF
        if duplicate_detected or k == ord('q') or count >= samples:
            break

    cam.release()
    cv2.destroyAllWindows()

    # Handle duplicate detection
    if duplicate_detected:
        raise ValueError("Registration aborted: This face already exists in the system!")

    # Save user info in DB
    add_user(user_id, name, email)
    print(f"[INFO] Collected {count} images for {name}.")
    return count


if __name__ == "__main__":
    # Manual test
    uid = input("Enter user id (unique): ").strip()
    name = input("Enter name: ").strip()
    email = input("Enter email: ").strip()
    try:
        register_user(uid, name, email, samples=30)
    except Exception as e:
        print("Error:", e)
