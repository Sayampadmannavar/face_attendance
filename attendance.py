# attendance.py
"""
Live attendance using webcam: recognizes faces and logs attendance + email.
"""

import cv2
import os
from db import add_attendance, get_user_by_userid
from email_notifier import send_attendance_email
from datetime import datetime
import time

CASCADE_PATH = os.path.join("haarcascades", "haarcascade_frontalface_default.xml")
TRAINER_DIR = "trainer"

def load_label_map():
    labels_path = os.path.join(TRAINER_DIR, "labels.txt")
    if not os.path.exists(labels_path):
        raise FileNotFoundError("labels.txt not found. Train model first.")
    mapping = {}
    with open(labels_path, "r") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            idx, uid = line.split(",", 1)
            mapping[int(idx)] = uid
    return mapping

def attend(threshold=70):
    """
    threshold: confidence threshold for LBPH — lower is better; adjust between 40-100 depending on camera/environment.
    """
    if not os.path.exists(os.path.join(TRAINER_DIR, "trainer.yml")):
        raise FileNotFoundError("trainer.yml not found. Run train.py first.")

    label_map = load_label_map()
    recognizer = cv2.face.LBPHFaceRecognizer_create()
    recognizer.read(os.path.join(TRAINER_DIR, "trainer.yml"))
    face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    cam = cv2.VideoCapture(0)

    last_logged = {}  # user_id -> last log timestamp to avoid duplicate logs within short span

    print("[INFO] Starting attendance. Press 'q' to quit.")
    while True:
        ret, img = cam.read()
        if not ret:
            break
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5)
        for (x, y, w, h) in faces:
            face_img = gray[y:y+h, x:x+w]
            label, confidence = recognizer.predict(face_img)  # lower confidence = better match
            text = "Unknown"
            if confidence < threshold and label in label_map:
                user_id = label_map[label]
                user = get_user_by_userid(user_id)
                if user:
                    name = user["name"]
                    text = f"{name} ({user_id}) - {confidence:.1f}"
                    # Avoid duplicate logging within, say, 30 seconds
                    now = time.time()
                    if user_id not in last_logged or (now - last_logged[user_id]) > 30:
                        add_attendance(user_id, status="Present")
                        timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        # send email (non-blocking idea: could spawn thread; for simplicity, call directly)
                        send_attendance_email(user["email"], user["name"], user_id, timestamp_str)
                        last_logged[user_id] = now
                else:
                    text = f"Unknown ({user_id})"
            else:
                text = f"Unknown - {confidence:.1f}"

            cv2.rectangle(img, (x,y), (x+w, y+h), (0,255,0), 2)
            cv2.putText(img, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0,255,0), 2)
        cv2.imshow("Attendance - Press q to Quit", img)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cam.release()
    cv2.destroyAllWindows()
    print("[INFO] Attendance stopped.")

if __name__ == "__main__":
    attend(threshold=70)
