import cv2
import numpy as np
import os
import time

qr_detector = cv2.QRCodeDetector()
detected_qr_data = set()

STATIC_FOLDER = os.path.join(os.path.dirname(__file__), 'static')
os.makedirs(STATIC_FOLDER, exist_ok=True)

QR_LOG_FILE = os.path.join(STATIC_FOLDER, 'qr_detected.log')


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
