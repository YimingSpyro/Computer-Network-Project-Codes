import cv2
import numpy as np
import io
import os
import sys
from flask import Flask, request, jsonify

app = Flask(__name__)

# Print debug info
print(f"Python version: {sys.version}")
print(f"OpenCV version: {cv2.__version__}")
print(f"Current directory: {os.getcwd()}")
print(f"Directory contents: {os.listdir('.')}")

# Create a basic route to verify the app is running
@app.route('/', methods=['GET'])
def home():
    return "Face verification service is running. Use POST /verify-face to submit an image."

# Initialize face detection and recognition with error handling
face_cascade = None
recognizer = None
AUTHORIZED_LABEL = 1
THRESHOLD = 55

@app.route('/initialize', methods=['GET'])
def initialize():
    global face_cascade, recognizer
    status = {}
    
    try:
        # Load the Haar cascade for face detection
        face_cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        status["cascade_path"] = face_cascade_path
        status["cascade_exists"] = os.path.exists(face_cascade_path)
        
        if not status["cascade_exists"]:
            status["cascade_error"] = "Haar cascade file not found"
        else:
            face_cascade = cv2.CascadeClassifier(face_cascade_path)
            status["cascade_loaded"] = True
            
        # Check if cv2.face is available
        status["has_face_module"] = hasattr(cv2, 'face')
        if not status["has_face_module"]:
            status["face_error"] = "OpenCV face module not available"
        else:
            # Create the LBPH face recognizer
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            status["recognizer_created"] = True
            
            # Load the model
            model_path = "model.xml"
            status["model_path"] = model_path
            status["model_exists"] = os.path.exists(model_path)
            
            if not status["model_exists"]:
                status["model_error"] = "Model file not found"
                status["directory_contents"] = os.listdir('.')
            else:
                recognizer.read(model_path)
                status["model_loaded"] = True
                status["success"] = True
        
    except Exception as e:
        status["error"] = str(e)
        status["error_type"] = type(e).__name__
    
    return jsonify(status)

@app.route('/webcam', methods=['GET'])
def webcam():
    with open('webcam.html', 'r') as f:
        return f.read()

@app.route('/verify-face', methods=['POST'])
def verify_face():
    # Check if the face recognition components were properly initialized
    if face_cascade is None or recognizer is None:
        return jsonify({"error": "Face recognition system not properly initialized. Check server logs."}), 500
        
    if 'image' not in request.files:
        return jsonify({"error": "No image file provided"}), 400

    try:
        file = request.files['image']
        in_memory_file = io.BytesIO()
        file.save(in_memory_file)
        data = np.frombuffer(in_memory_file.getvalue(), dtype=np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)

        if img is None:
            return jsonify({"error": "Invalid image"}), 400

        # Convert to grayscale and normalize lighting
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        # Detect faces
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5)
        if len(faces) == 0:
            return jsonify({"error": "No face detected"}), 400

        # Use the first detected face
        (x, y, w, h) = faces[0]
        face_roi = gray[y:y+h, x:x+w]
        face_roi = cv2.resize(face_roi, (200, 200))

        # Predict label and confidence
        label_pred, confidence = recognizer.predict(face_roi)
        result = "Authenticated" if label_pred == AUTHORIZED_LABEL and confidence < THRESHOLD else "Not Authenticated"

        return jsonify({"result": result, "label": label_pred, "confidence": confidence})
    except Exception as e:
        print(f"Error processing image: {e}")
        return jsonify({"error": f"Error processing image: {str(e)}"}), 500

# Add a test endpoint that doesn't require image processing
@app.route('/test', methods=['GET'])
def test():
    return jsonify({"status": "ok", "message": "Server is running"})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=5000, debug=True)