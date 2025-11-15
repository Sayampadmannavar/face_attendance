# train.py
"""
Train LBPH face recognizer on images in dataset/.
Assumes filenames like <user_id>_<count>.jpg
Saves:
  - trainer/trainer.yml (trained model)
  - trainer/labels.txt (mapping: <int_label>,<user_id>)
"""

import cv2
import os
import numpy as np
from collections import defaultdict

DATASET_DIR = "dataset"
TRAINER_DIR = "trainer"
CASCADE_PATH = os.path.join("haarcascades", "haarcascade_frontalface_default.xml")

def train():
    os.makedirs(TRAINER_DIR, exist_ok=True)
    image_paths = [os.path.join(DATASET_DIR, f) for f in os.listdir(DATASET_DIR) if f.endswith(".jpg")]
    if not image_paths:
        raise RuntimeError("No images in dataset/. Register users first.")

    # Build mapping user_id -> numeric label
    user_ids = sorted({os.path.basename(p).split("_")[0] for p in image_paths})
    label_map = {uid: idx for idx, uid in enumerate(user_ids)}

    faces = []
    labels = []
    for img_path in image_paths:
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            continue
        basename = os.path.basename(img_path)
        uid = basename.split("_")[0]
        label = label_map[uid]
        faces.append(img)
        labels.append(label)

    faces_np = faces  # LBPH accepts list of numpy arrays
    labels_np = np.array(labels)

    recognizer = cv2.face.LBPHFaceRecognizer_create()
    print("[INFO] Training LBPH recognizer on", len(faces_np), "faces...")
    recognizer.train(faces_np, labels_np)
    model_path = os.path.join(TRAINER_DIR, "trainer.yml")
    recognizer.write(model_path)
    print(f"[INFO] Saved trainer at {model_path}")

    # Save labels mapping
    labels_path = os.path.join(TRAINER_DIR, "labels.txt")
    with open(labels_path, "w") as f:
        for uid, idx in label_map.items():
            f.write(f"{idx},{uid}\n")
    print(f"[INFO] Saved label map at {labels_path}")

if __name__ == "__main__":
    train()
