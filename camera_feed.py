# server_socket_cam.py (Run this on your Raspberry Pi)

import socket
import cv2
import struct
import time
import os

# --- Import your QR code logic ---
# This assumes your qr.py is in the same directory.
# We'll call qr() to process the frame before sending.
from qr import qr # Just need the qr function for processing

# --- Camera Initialization ---
# Using the native V4L2 backend, which you confirmed worked in recent tests.
CAMERA_INDEX = 0 
GST_PIPELINE = ( # Fallback if native V4L2 doesn't work, but try direct first
    "v4l2src device=/dev/video0 ! "
    "image/jpeg,width=640,height=480,framerate=30/1 ! "
    "jpegdec ! videoconvert ! video/x-raw,format=BGR ! appsink drop=true max-buffers=1"
)

# --- Socket Setup ---
PORT = 8485 # Port to listen on

def main():
    print("Starting camera socket server on Pi...")

    # --- Initialize Camera (Robustly) ---
    cap = None
    max_retries = 3
    retry_delay = 1 

    for i in range(max_retries):
        print(f"Attempting to open camera (Attempt {i+1}/{max_retries})...")
        # Try native V4L2 first (simpler)
        cap = cv2.VideoCapture(CAMERA_INDEX, cv2.CAP_V4L2) 
        
        # Set properties explicitly for native V4L2
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        cap.set(cv2.CAP_PROP_FPS, 30)

        if cap.isOpened():
            print("Camera opened successfully.")
            break 
        else:
            print(f"WARNING: Camera failed to open on attempt {i+1} with native V4L2. Retrying with GStreamer pipeline...")
            cap = cv2.VideoCapture(GST_PIPELINE, cv2.CAP_GSTREAMER) # Try GStreamer pipeline
            if cap.isOpened():
                print("Camera opened successfully with GStreamer pipeline.")
                break
            else:
                print(f"WARNING: Camera failed to open on attempt {i+1} with GStreamer too. Retrying in {retry_delay} seconds...")
                if cap: cap.release()
                time.sleep(retry_delay)

    if not cap or not cap.isOpened():
        print("CRITICAL ERROR: Failed to open camera after multiple retries. Exiting.")
        return # Exit if camera fails

    # --- Socket Setup ---
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        server_socket.bind(('', PORT)) # Bind to all available interfaces
        server_socket.listen(1) # Listen for one client connection
        print(f"[SERVER] Listening on port {PORT}. Waiting for client connection...")
        conn, addr = server_socket.accept()
        print(f"[SERVER] Connected to client: {addr}")
    except socket.error as e:
        print(f"[SERVER] Socket error: {e}. Exiting.")
        cap.release()
        server_socket.close()
        return

    # --- Main Streaming Loop ---
    try:
        while True:
            ret, frame = cap.read() # Read a frame from the camera
            if not ret:
                print("Failed to grab frame from camera. Breaking stream loop.")
                break

            # Process frame with QR detection (from your qr.py)
            processed_frame = qr(frame) # qr() function also prints to terminal
            
            if processed_frame is None: # Fallback if qr() function returns None
                processed_frame = frame

            # Encode the frame as JPEG
            _, buffer = cv2.imencode('.jpg', processed_frame)
            data = buffer.tobytes()
            size = len(data)

            # Send size and then the data
            conn.sendall(struct.pack(">L", size)) # Pack size as unsigned long (4 bytes)
            conn.sendall(data)

    except (socket.error, BrokenPipeError) as e:
        print(f"[SERVER] Client disconnected or socket error: {e}")
    except KeyboardInterrupt:
        print("\n[SERVER] Server stopped by user.")
    finally:
        print("[SERVER] Cleaning up...")
        cap.release()
        if 'conn' in locals() and conn: # Check if conn was established
            conn.close()
        server_socket.close()
        print("[SERVER] Cleanup complete.")

if __name__ == "__main__":
    main()