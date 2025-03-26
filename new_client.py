import tkinter as tk
from tkinter import Label, Button, Frame
import cv2
import requests
import threading
from PIL import Image, ImageTk
import io

# Updated endpoint URL to point to the bank authentication server
FACE_SERVER_URL = "http://axial-sunup-454015-m4.uc.r.appspot.com/verify-face"
INVENTORY_SERVER_URL = "http://localhost:5001/update-inventory"

# Global shopping list dictionary
shopping_list = {
    "apple": 0,
    "banana": 0
}

# Initialize the video capture once (global object)
cap = cv2.VideoCapture(0)

def update_labels():
    """Refresh the label texts to reflect current quantities."""
    apple_label.config(text=f"Apple: {shopping_list['apple']}")
    banana_label.config(text=f"Banana: {shopping_list['banana']}")

def update_message(msg, color="red"):
    """Update the message label with a new message and optional color."""
    message_label.config(text=msg, fg=color)

def add_apple():
    shopping_list["apple"] += 1
    update_labels()

def sub_apple():
    if shopping_list["apple"] > 0:
        shopping_list["apple"] -= 1
    update_labels()

def add_banana():
    shopping_list["banana"] += 1
    update_labels()

def sub_banana():
    if shopping_list["banana"] > 0:
        shopping_list["banana"] -= 1
    update_labels()

def capture_and_update():
    """Capture the current frame, verify face, and update inventory if authenticated."""
    ret, frame = cap.read()
    if not ret:
        msg = "Failed to capture frame."
        print(msg)
        root.after(0, update_message, msg)
        return

    # Encode the frame to JPEG in memory
    ret, buffer = cv2.imencode('.jpg', frame)
    if not ret:
        msg = "Failed to encode frame."
        print(msg)
        root.after(0, update_message, msg)
        return

    img_bytes = io.BytesIO(buffer)

    # Send face recognition request
    try:
        response_face = requests.post(FACE_SERVER_URL, files={"image": img_bytes})
    except requests.exceptions.RequestException as e:
        msg = f"Error during request to face server: {e}"
        print(msg)
        root.after(0, update_message, msg)
        return

    try:
        face_response = response_face.json()
    except Exception as e:
        msg = f"Error processing face recognition response: {e}. Raw response: {response_face.text}"
        print(msg)
        root.after(0, update_message, msg)
        return

    print("Face server response:", face_response)

    # If authentication is confirmed, send inventory update
    if face_response.get("result") == "Authenticated":
        payload = {"items_sold": shopping_list}
        try:
            response_inventory = requests.post(INVENTORY_SERVER_URL, json=payload, timeout=10)
            inv_response = response_inventory.json()
            msg = f"Inventory update response: {inv_response}"
            print(msg)
            root.after(0, update_message, msg, "green")
        except requests.exceptions.RequestException as e:
            msg = f"Error during request to inventory server: {e}"
            print(msg)
            root.after(0, update_message, msg)
    else:
        msg = "Authentication failed. Inventory update not sent."
        print(msg)
        root.after(0, update_message, msg)

def capture_thread():
    """Run capture_and_update in a separate thread to keep the UI responsive."""
    threading.Thread(target=capture_and_update, daemon=True).start()

def update_video_feed():
    """Continuously update the video feed in the Tkinter UI."""
    ret, frame = cap.read()
    if ret:
        # Convert frame color from BGR to RGB
        cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        # Convert to PIL image
        img = Image.fromarray(cv2image)
        # Convert to ImageTk format
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk  # Keep a reference to avoid garbage collection
        video_label.config(image=imgtk)
    # Schedule the next frame update
    video_label.after(10, update_video_feed)

# Set up the Tkinter UI
root = tk.Tk()
root.title("Inventory Control with Face Preview")

# Video feed display label
video_label = Label(root)
video_label.pack(pady=10)
update_video_feed()

# Labels for current counts
apple_label = tk.Label(root, text="Apple: 0", font=("Helvetica", 14))
apple_label.pack(pady=5)

banana_label = tk.Label(root, text="Banana: 0", font=("Helvetica", 14))
banana_label.pack(pady=5)

# Message label for errors or status messages
message_label = tk.Label(root, text="", font=("Helvetica", 12))
message_label.pack(pady=5)

# Buttons for adjusting apples
btn_frame1 = Frame(root)
btn_frame1.pack(pady=5)
Button(btn_frame1, text="Add Apple", command=add_apple, width=15).grid(row=0, column=0, padx=5)
Button(btn_frame1, text="Subtract Apple", command=sub_apple, width=15).grid(row=0, column=1, padx=5)

# Buttons for adjusting bananas
btn_frame2 = Frame(root)
btn_frame2.pack(pady=5)
Button(btn_frame2, text="Add Banana", command=add_banana, width=15).grid(row=0, column=0, padx=5)
Button(btn_frame2, text="Subtract Banana", command=sub_banana, width=15).grid(row=0, column=1, padx=5)

# Button to capture face and update inventory
capture_btn = Button(root, text="Capture & Update", command=capture_thread, width=32, bg="lightblue")
capture_btn.pack(pady=10)

def on_closing():
    cap.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", on_closing)
root.mainloop()
