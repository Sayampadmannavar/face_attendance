# attendance.py
"""
Live attendance using webcam: recognizes faces and logs attendance + email.
Optimized with lazy loading and model caching for faster startup.
"""

import os
from db import add_attendance, get_user_by_userid
from datetime import datetime
import time
import threading

CASCADE_PATH = os.path.join("haarcascades", "haarcascade_frontalface_default.xml")
TRAINER_DIR = "trainer"

# Lazy-loaded and cached modules
_cv2 = None
_recognizer = None
_face_cascade = None
_label_map = None

def _lazy_import_cv2():
    """Import cv2 only when first needed."""
    global _cv2
    if _cv2 is None:
        import cv2
        _cv2 = cv2
    return _cv2

def _lazy_load_model():
    """Load LBPH recognizer and cascade classifier once (cached)."""
    global _recognizer, _face_cascade, _label_map
    if _recognizer is not None and _face_cascade is not None:
        return _recognizer, _face_cascade, _label_map
    
    cv2 = _lazy_import_cv2()
    
    # Load label map
    labels_path = os.path.join(TRAINER_DIR, "labels.txt")
    if not os.path.exists(labels_path):
        raise FileNotFoundError("labels.txt not found. Train model first.")
    mapping = {}
    with open(labels_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            idx, uid = line.split(",", 1)
            mapping[int(idx)] = uid
    _label_map = mapping
    
    # Load LBPH recognizer
    if not os.path.exists(os.path.join(TRAINER_DIR, "trainer.yml")):
        raise FileNotFoundError("trainer.yml not found. Run train.py first.")
    _recognizer = cv2.face.LBPHFaceRecognizer_create()
    _recognizer.read(os.path.join(TRAINER_DIR, "trainer.yml"))
    
    # Load cascade classifier
    _face_cascade = cv2.CascadeClassifier(CASCADE_PATH)
    
    return _recognizer, _face_cascade, _label_map

def attend(threshold=70):
    """
    threshold: confidence threshold for LBPH — lower is better; adjust between 40-100 depending on camera/environment.
    """
    cv2 = _lazy_import_cv2()
    recognizer, face_cascade, label_map = _lazy_load_model()
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
                        # send email asynchronously (non-blocking) to avoid slowing down attendance
                        try:
                            from email_notifier import send_attendance_email
                            thread = threading.Thread(
                                target=send_attendance_email,
                                args=(user["email"], user["name"], user_id, timestamp_str),
                                daemon=True
                            )
                            thread.start()
                        except Exception as e:
                            print(f"[WARN] Could not send email async: {e}")
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
