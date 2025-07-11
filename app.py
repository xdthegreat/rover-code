from flask import Flask, request, jsonify, render_template, Response
import cv2
import time

import threading
import json
import math

from hardware import forward, backward, turn_left, turn_right, stop #comment and uncomment while running 
from qr import *
import serial # <--- REQUIRED: For serial communication used by ArduinoSerialComm
from serial_comm import ArduinoSerialComm 
import logging
import board
import busio
from servo_cam import CameraServoController
from kinematics import SkidSteerOdometry, track_width_m

app = Flask(__name__)

# --- NEW: Code to suppress specific log messages ---
log = logging.getLogger('werkzeug') # Get the werkzeug logger (used by Flask's dev server)

class NoEncoderGetFilter(logging.Filter):
    def filter(self, record):
        # Only log requests that are NOT for /get_encoder_data
        return not ("/get_encoder_data" in record.getMessage() and "GET" in record.getMessage())

log.addFilter(NoEncoderGetFilter()) # Apply the filter to the logger
# --- END NEW Code ---

SERIAL_PORT_MEGA = "/dev/ttyACM0"  # Adjust to your Arduino's serial device
BAUD_RATE_MEGA = 115200           # Adjust to match your Arduino's Serial.begin() baud rate

# --- REQUIRED: Instantiate the ArduinoSerialComm for encoder data ---
arduino_comm = ArduinoSerialComm(SERIAL_PORT_MEGA, BAUD_RATE_MEGA)

# --- REQUIRED: Global variables for encoder data and thread safety ---
latest_encoder_data = {
    'rpm1': 0.0, 'speed1': 0.0,
    'rpm2': 0.0, 'speed2': 0.0,
    'yaw': 0.0 # Assuming yaw is also part of the encoder data
    
}
encoder_data_lock = threading.Lock() # Protects access to latest_encoder_data

odometry = SkidSteerOdometry(track_width_m) # Uses track_width_m

# --- REQUIRED: Thread function to continuously read encoder data from Arduino ---
def read_encoder_data_thread(ser_comm_obj):
    global latest_encoder_data # Declare intent to modify global variable
    print("[Encoder Thread] Starting to read encoder data...")
    while True:
        try:
            line = ser_comm_obj.read_data() # Use the read_data method from ArduinoSerialComm
            if line:
                parts = line.split(",")
                if len(parts) == 7:
                    try:
                        # Parse float values
                        imu_yaw_deg  = float(parts[0]) 
                        rpm1 = float(parts[3])
                        speed1 = float(parts[4])
                        rpm2 = float(parts[5])
                        speed2 = float(parts[6])
                        
                        
                        with encoder_data_lock: # Acquire lock before modifying shared data
                            latest_encoder_data = {
                                'rpm1': rpm1, 'speed1': speed1,
                                'rpm2': rpm2, 'speed2': speed2
                                
                            }
                        # print(f"[Encoder Thread] Updated Data: {latest_encoder_data}") 

                        # --- NEW: Update Odometry ---
                        # Assuming rpm1 is left wheel RPM, rpm2 is right wheel RPM
                        odometry.update(rpm1, rpm2, imu_yaw_deg )
                        x, y, theta_deg = odometry.get_pose()
                        # print(f"[Odometry] X: {x:.3f} m, Y: {y:.3f} m, Theta: {theta_deg:.1f}°") # Debug print for odometry
                    except ValueError:
                        print(f"[Encoder Thread] Parse error for encoder data: {line}")
                else:
                    print(f"[Encoder Thread] Invalid line format: {line}")
            else:
                # No data to read or serial connection might be down
                if not ser_comm_obj.ser or not ser_comm_obj.ser.is_open:
                    print("[Encoder Thread] Serial not open, pausing read attempts.")
                    time.sleep(5) # Pause longer if serial is completely disconnected
                else:
                    time.sleep(0.05) # Small delay to prevent busy-looping if no data available yet
        except Exception as e:
            print(f"[Encoder Thread] Unexpected error processing encoder data: {e}")
            time.sleep(1) # Sleep on error to prevent rapid crashes


current_global_motor_speed = 50

@app.route('/')
def index():
    return render_template('index_g.html')

@app.route('/send_command', methods=['POST'])
def send_command():
    data = request.get_json()
    command = data.get('command')
    print(f"Received command: {command}", flush=True)
    if command == 'forward':
        forward(current_global_motor_speed) # <--- The global speed is passed here!
    elif command == 'backward':
        backward(current_global_motor_speed) # <--- The global speed is passed here!
    elif command == 'left':
        turn_left(current_global_motor_speed) # <--- The global speed is passed here!
    elif command == 'right':
        turn_right(current_global_motor_speed) # <--- The global speed is passed here!
    elif command == 'stop':
        stop() # Stop doesn't need a speed, as it sets PWM to 0
    else:
        print(f"Unknown command received: {command}")
        
    return jsonify({'status': 'success', 'command': command})

# ######################## Added for getting speed from html
@app.route('/set_global_speed', methods=['POST'])
def set_global_speed():
    global current_global_motor_speed # Declare intent to modify the global variable
    data = request.get_json()
    speed = data.get('speed') # <-- This is where the '75' from the frontend arrives!
    
    if isinstance(speed, int) and speed >= 0 and speed <= 100:
        current_global_motor_speed = speed # <-- The global variable is updated here
        print(f"Global motor speed set to: {current_global_motor_speed}%", flush=True)
        return jsonify({'status': 'success', 'speed': speed})
 #############################
 #for encoder data
@app.route('/get_encoder_data')
def get_encoder_data():
    with encoder_data_lock: # Acquire lock before reading shared data
        data = latest_encoder_data
    # print(f"[Flask API] Sending Encoder Data: {data}") # Uncomment for API response debugging
    return jsonify(data)   

# --- to get Odometry Pose ---
@app.route('/get_pose')
def get_pose():
    with encoder_data_lock: # Use the same lock as encoder data for consistency
        x, y, theta_deg = odometry.get_pose()
    return jsonify({'x': x, 'y': y, 'theta': theta_deg})
    

# ---  DELAY FOR CAMERA ---
print("Delaying for camera warm-up...")
time.sleep(5) # Wait 5 seconds to ensure camera is fully initialized

cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 320)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 240)

qr_detector = cv2.QRCodeDetector()
detected_qr_data = set()

def gather_img():
    while True:
        ret, img = cam.read()
        if not ret:
            print("Failed to grab frame from camera. Exiting stream.")
            break
        img = qr(img)
        _, frame = cv2.imencode('.jpg', img)
        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame.tobytes() + b'\r\n')
        time.sleep(0.1)

@app.route("/mjpeg")
def mjpeg():
    return Response(gather_img(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/send_angle', methods=['POST'])
def send_angle():
    data = request.get_json()
    angle = data.get('angle')
    print(f"Received angle: {angle}", flush=True)
    # change_angle()
    # --- NEW: Call set_camera_tilt_angle from CameraServoController object ---
    camera_servo_controller.set_angle(angle) 
    return jsonify({'status': 'success', 'angle': angle})

if __name__ == '__main__':
    print("Starting Flask application...")

    # --- Initial Camera Check ---
    print("Initializing camera...")
    if not cam.isOpened():
        print("CRITICAL ERROR: Failed to open camera using GStreamer pipeline.")
        print("Please check: 1. USB camera connected? 2. '/dev/video0' is correct? 3. GStreamer/OpenCV installation.")
        # import sys; sys.exit(1) # Consider exiting if camera is critical for operation
    else:
        print("Camera opened successfully.")

    # --- REQUIRED: RPi.GPIO init and Encoder Thread Start (moved before app.run) ---
    print("RPi.GPIO motor control ready via hardware.py.")
    
    # NEW: Initialize I2C bus here for all PCA9685 communication
    i2c_bus = busio.I2C(board.SCL, board.SDA) 
    SERVO_CAM_PCA_ADDRESS = 0x40 # Example: Address for the PCA9685 controlling the camera servo
    CAMERA_TILT_SERVO_CHANNEL = 3 
    # Initialize the Camera Servo Controller pca_address, servo_channel
    camera_servo_controller = CameraServoController(i2c_bus, SERVO_CAM_PCA_ADDRESS, CAMERA_TILT_SERVO_CHANNEL)
    if camera_servo_controller.pca is None:
        print("CRITICAL ERROR: Camera Servo PCA9685 not initialized. Camera tilt control unavailable.")
    else:
        print("Camera Servo PCA9685 initialized.")


    print("PCA9685 motor control ready via hardware.py.") 
    
    if arduino_comm.ser is None: # Check if serial connection failed at startup
        print("CRITICAL ERROR: Arduino serial communication not established for encoder data.")
        # import sys; sys.exit(1) # Consider exiting if encoder data is critical
    else:
        print("Arduino serial communication ready for encoder data.")
        # Start the encoder reading thread ONLY if serial is connected
        encoder_read_thread = threading.Thread(target=read_encoder_data_thread, args=(arduino_comm,), daemon=True)
        encoder_read_thread.start()
        print("Encoder data reading thread started.")

    try:
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)
    except KeyboardInterrupt:
        print("\nFlask app interrupted by user. Performing cleanup...")
    except Exception as e:
        print(f"\nAn unexpected error occurred: {e}. Performing cleanup...")
    finally:
        if cam:
            cam.release()
            print("Camera released.")
        # arduino_comm.close() is handled for daemon thread exit by Python.
        # It's also handled by the ArduinoSerialComm's __del__ if implemented, or on process exit.
        # cleanup_gpio() # This cleans up RPi.GPIO pins from hardware.py
        # print("Application cleanup complete.")

