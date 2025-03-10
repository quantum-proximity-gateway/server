import os
from imutils import paths
import face_recognition
import pickle
import cv2

def train_model(frame_paths, username):
    print("[INFO] start processing faces...")

    if os.path.exists("encodings.pickle") and os.path.getsize("encodings.pickle") > 0:
        with open("encodings.pickle", "rb") as f:
            data = pickle.loads(f.read())
        knownEncodings = data['encodings']
        knownNames = data['names']
    else:
        knownEncodings = []
        knownNames = []

    for (i, imagePath) in enumerate(frame_paths):
        print(f"[INFO] processing image {i + 1}/{len(frame_paths)}")
        
        image = cv2.imread(imagePath)
        if image is None:
            print(f"[WARNING] could not read image {imagePath}, skipping.")
            continue
        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        boxes = face_recognition.face_locations(rgb, model="hog")
        encodings = face_recognition.face_encodings(rgb, boxes)
        
        for encoding in encodings:
            knownEncodings.append(encoding)
            knownNames.append(username)

    print("[INFO] serializing encodings...")
    data = {"encodings": knownEncodings, "names": knownNames}
    print(data)
    with open("encodings.pickle", "wb") as f:
        f.write(pickle.dumps(data))

    print("[INFO] Training complete. Encodings saved to 'encodings.pickle'")