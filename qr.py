import cv2
import numpy as np
import os
import time
import base64


# cam = cv2.VideoCapture(1)
# cam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
# cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

qr_detector = cv2.QRCodeDetector()
detected_qr_data = set()

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
os.makedirs(STATIC_FOLDER, exist_ok=True)

QR_LOG_FILE = os.path.join(STATIC_FOLDER, 'qr_detected.log')

DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(DATA_FOLDER, exist_ok=True)
QR_LOG_FILE = os.path.join(DATA_FOLDER, 'qr_detected.log')

# def take_pic():
#     """Capture a photo without releasing the camera (no crash)."""
#     ret, frame = cam.read()
#     if not ret:
#         print("Failed to capture image")
#         return False

#     image_filename = f"undecoded_qr_{int(time.time())}.jpg"  
#     image_path = os.path.join(DATA_FOLDER, image_filename)
#     cv2.imwrite(image_path, frame)
#     print(f"[QR] Saved image: {image_path}")
            
#     with open(QR_LOG_FILE, "a") as f:
#         f.write(f"{time.ctime()} - (Image: {image_filename})\n")
#     print(f"[QR] Logged to {QR_LOG_FILE}")

#     with open('data/qr.html', 'a') as f:
#         f.write(f'<div style="border: 5px solid red; width: fit-content;"> <img src="undecoded_qr_{int(time.time())}.jpg"><br> </div>')
#         f.write(f'<div style="color: red;"> Missing data </div>')
#     print("[QR] Image data saved to qr.html")
#     return True

# def gather_img():
#     """MJPEG stream generator."""
#     while True:
#         ret, img = cam.read()
#         if not ret:
#             print("Failed to grab frame from camera. Exiting stream.")
#             break
#         img = qr(img)
#         _, frame = cv2.imencode('.jpg', img)
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n')
#         time.sleep(0.1)

def qr(img):
    data, bbox, _ = qr_detector.detectAndDecode(img)
    if data:
        if data not in detected_qr_data:
            print(f"[QR] New QR Code Detected: {data}")
            detected_qr_data.add(data)
            filename = f"qr_{len(detected_qr_data)}.jpg"
            cv2.imwrite(filename, img)
            with open("qrs.html", "a") as f:
                f.write(f'<div> <img src="qr_{len(detected_qr_data)}.jpg"><br> </div>')
                f.write(f'<div> {data} </div>')
            
            image_filename = f"qr_{len(detected_qr_data)}_{int(time.time())}.jpg" 
            image_path = os.path.join(STATIC_FOLDER, image_filename)
            cv2.imwrite(image_path, img)
            print(f"[QR] Saved image: {image_path}")
            
            with open(QR_LOG_FILE, "a") as f:
                f.write(f"{time.ctime()} - {data} (Image: {image_filename})\n")
            print(f"[QR] Logged to {QR_LOG_FILE}")

        if bbox is not None:
            bbox = bbox.astype(int)
            for i in range(len(bbox[0])):
                pt1 = tuple(bbox[0][i])
                pt2 = tuple(bbox[0][(i + 1) % len(bbox[0])])
                cv2.line(img, pt1, pt2, (0, 255, 0), 2)
    if bbox is not None:
        bbox = bbox.astype(int)
        for i in range(len(bbox[0])):
            pt1 = tuple(bbox[0][i])
            pt2 = tuple(bbox[0][(i + 1) % len(bbox[0])])
            cv2.line(img, pt1, pt2, (0, 255, 0), 2)
            if data:
                cv2.putText(img, data, (bbox[0][0][0], bbox[0][0][1] - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                #cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    return img
