import cv2
import os
import numpy as np

# Define folders for authorized and unauthorized images
authorized_dir = "authorized_images"
unauthorized_dir = "unauthorized_images"

faces = []
labels = []

# Load the Haar cascade for face detection
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

# Define labels for each class
AUTHORIZED_LABEL = 1
UNAUTHORIZED_LABEL = 0

def process_images(directory, label):
    for filename in os.listdir(directory):
        if filename.lower().endswith((".jpg", ".jpeg", ".png")):
            path = os.path.join(directory, filename)
            img = cv2.imread(path)
            if img is None:
                continue
            # Convert to grayscale and equalize histogram for normalization
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            # Detect faces in the image
            detected_faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
            for (x, y, w, h) in detected_faces:
                face_roi = gray[y:y+h, x:x+w]
                # Resize to a fixed size (e.g., 200x200) for consistency
                face_roi = cv2.resize(face_roi, (200, 200))
                faces.append(face_roi)
                labels.append(label)

# Process authorized images
process_images(authorized_dir, AUTHORIZED_LABEL)
# Process unauthorized images
process_images(unauthorized_dir, UNAUTHORIZED_LABEL)

if len(faces) == 0:
    print("No faces found in training images.")
    exit(1)

# Create and train the LBPH face recognizer
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces, np.array(labels))
recognizer.write("model.xml")
print("Training complete. Model saved as model.xml.")
