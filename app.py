# app.py - Flask Web Application for Rover Control
# This application provides a web interface to control a rover using motors and an IMU sensor.  
# It includes features for motor control, camera streaming, and QR code detection.


from flask import Flask, request, jsonify, render_template, Response , send_from_directory
import cv2
import time

import threading
import json
import math

import os # Ensure os is imported at the top of app.py if not already

# --- NEW: Global variable for the latest camera frame and a lock for thread safety ---
latest_camera_frame = None
camera_frame_lock = threading.Lock() #

from hardware import forward, backward, turn_left, turn_right, stop
from qr import * # <--- REQUIRED: For QR code detection and camera streaming
import serial # <--- REQUIRED: For serial communication used by ArduinoSerialComm
from serial_comm import ArduinoSerialComm   # <--- REQUIRED: For Arduino serial communication
import logging # <--- REQUIRED: For logging configuration
import board # <--- REQUIRED: For board pin definitions
import adafruit_pca9685 # <--- REQUIRED: For PCA9685 servo control
import busio # <--- REQUIRED: For I2C communication used by PCA9685
from servo_cam import CameraServoController # <--- REQUIRED: For camera servo control
from kinematics import SkidSteerOdometry, track_width_m # <--- REQUIRED: For odometry calculations

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
    'yaw': 0.0 # Added yaw for odometry calculations
    
}
encoder_data_lock = threading.Lock() # Protects access to latest_encoder_data

odometry = SkidSteerOdometry(track_width_m) # Uses track_width_m

# --- NEW: Automation Global Variables and Thread Event ---
automation_active = threading.Event() # Event to signal the automation thread to run
automation_target_distance = 0.0 # meters
automation_target_direction = 0.0 # degrees
automation_speed = 30 # Default speed for automation (in %)
automation_state = "IDLE" # For internal tracking/display:

# --- REQUIRED: Thread function to continuously read encoder data from Arduino ---
def read_encoder_data_thread(ser_comm_obj):
    global latest_encoder_data # Declare intent to modify global variable
    print("[Encoder Thread] Starting to read encoder data...")

    from __main__ import app # Import 'app' from the global scope of app.py

    while True:
        with app.app_context():
            try:
                line = ser_comm_obj.read_data() # Use the read_data method from ArduinoSerialComm
                if line:
                    parts = line.split(",")
                    if len(parts) == 7:
                        try:
                            # Parse float values 
                            # Assuming the format is: "imu_yaw_deg,rpm1,speed1,rpm2,speed2"
                            # Example: "45.0,100,50,120,60"
                            imu_yaw_deg  = float(parts[0]) 
                            imu_pitch_deg = float(parts[1]) # NEW: Parse IMU Pitch
                            imu_roll_deg  = float(parts[2]) # NEW: Parse IMU Roll   
                            rpm1 = float(parts[3])  
                            speed1 = float(parts[4]) 
                            rpm2 = float(parts[5]) 
                            speed2 = float(parts[6]) 
                            
                            # Update the latest encoder data
                            # Use a lock to ensure thread safety when updating shared data
                            with encoder_data_lock: # Acquire lock before modifying shared data
                                latest_encoder_data = {
                                    'rpm1': rpm1, 'speed1': speed1, 
                                    'rpm2': rpm2, 'speed2': speed2, 
                                    'yaw': imu_yaw_deg,   # NEW: Store Yaw
                                    'pitch': imu_pitch_deg, # NEW: Store Pitch
                                    'roll': imu_roll_deg  # NEW: Store Roll
                                }
                            # print(f"[Encoder Thread] Updated Data: {latest_encoder_data}") 

                            # --- NEW: Update Odometry ---
                            # Assuming rpm1 is left wheel RPM, rpm2 is right wheel RPM
                            odometry.update(rpm1, rpm2, imu_yaw_deg )
                            # x, y, theta_deg = odometry.get_pose()
                            
    #                         return jsonify({
    #                             'x': x, 'y': y, 'theta': theta_deg,
    #                             'distance': absolute_distance # This value is sent to the frontend
    # })
                            # print(f"[Odometry] X: {x:.3f} m, Y: {y:.3f} m, Theta: {theta_deg:.1f}°") # Debug print for odometry
                        except ValueError:
                            print(f"[Encoder Thread] Parse error for encoder data: {line}")
                    else:
                        print(f"[Encoder Thread] Invalid line format: {line} - expected 7 parts, got {len(parts)}")
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

def automation_control_thread():
    global automation_state, automation_active # Need to modify automation_state and automation_active event
    print("[Automation Thread] Starting automation control loop...")

    from __main__ import app # For app.app_context()

    while True: # This loop runs continuously in the background
        automation_active.wait() # This blocks the thread until automation_active.set() is called

        print(f"[Automation Thread] Automation activated. Target Distance: {automation_target_distance}m, Target Direction: {automation_target_direction}°")
        
        with app.app_context(): # Ensure Flask context for logging, or if calling Flask globals
            try:
                # --- Get initial pose for distance calculation ---
                with encoder_data_lock:
                    initial_x, initial_y, initial_theta_deg = odometry.get_pose()
                
                # --- Step 1: Turn to Target Direction ---
                automation_state = "TURNING"
                print(f"[Automation Thread] State: TURNING. Current Theta: {initial_theta_deg:.1f}°, Target: {automation_target_direction}°")
                angle_tolerance = 2.0 # Degrees +/- for alignment
                turn_speed = automation_speed # Use automation speed for turning

                # Turn loop: continues until aligned or automation is stopped
                while automation_active.is_set():
                    with encoder_data_lock: # Access shared odometry data
                        current_x, current_y, current_theta_deg = odometry.get_pose()
                    
                    angle_error = automation_target_direction - current_theta_deg
                    angle_error = odometry.normalize_angle_deg(angle_error) # Normalize error to -180 to 180

                    if abs(angle_error) <= angle_tolerance:
                        print(f"[Automation Thread] Angle aligned. Current: {current_theta_deg:.1f}°")
                        stop() # Stop motors once aligned
                        break # Exit turning loop
                    
                    # Command appropriate turn
                    if angle_error > 0: # Positive error means target is to the left
                        turn_left(turn_speed)
                        print(f"[Automation Thread] Turning left, error: {angle_error:.1f}°")
                    else: # Negative error means target is to the right
                        turn_right(turn_speed)
                        print(f"[Automation Thread] Turning right, error: {angle_error:.1f}°")
                    
                    time.sleep(0.05) # Small delay to avoid busy-waiting

                # Check if automation was stopped during turn phase
                if not automation_active.is_set(): 
                    stop()
                    automation_state = "IDLE"
                    print("[Automation Thread] Automation stopped during turn.")
                    continue # Go back to waiting for next activation

                # --- Step 2: Drive to Target Distance ---
                automation_state = "DRIVING"
                print(f"[Automation Thread] State: DRIVING. Target Distance: {automation_target_distance}m")
                drive_speed = automation_speed # Use automation speed for driving
                distance_driving_tolerance = 0.05 # Meters, how close to target distance to stop

                # Driving loop: continues until distance reached or automation stopped
                while automation_active.is_set():
                    with encoder_data_lock: # Access shared odometry data
                        current_x, current_y, current_theta_deg = odometry.get_pose()
                    
                    # Calculate distance traveled from the point automation was activated
                    distance_traveled = math.sqrt((current_x - initial_x)**2 + (current_y - initial_y)**2)
                    distance_remaining = automation_target_distance - distance_traveled

                    if distance_remaining <= distance_driving_tolerance: 
                        print(f"[Automation Thread] Distance reached. Traveled: {distance_traveled:.2f}m")
                        stop()
                        break # Exit driving loop
                    
                    # Optional: Re-align heading slightly during driving if drift occurs (more advanced PID control)
                    
                    forward(drive_speed) # Drive forward
                    print(f"[Automation Thread] Driving, remaining: {distance_remaining:.2f}m")
                    time.sleep(0.05) 

                # Check if automation was stopped during drive phase
                if not automation_active.is_set(): 
                    stop()
                    automation_state = "IDLE"
                    print("[Automation Thread] Automation stopped during drive.")
                    continue # Go back to waiting for next activation

                # --- Step 3: Finished ---
                automation_state = "FINISHED"
                stop()
                print("[Automation Thread] Automation sequence completed.")
                
            except Exception as e:
                print(f"[Automation Thread] CRITICAL ERROR in control loop: {e}")
                stop() # Attempt to stop motors on error
            finally:
                automation_active.clear() # Clear the event, so it waits for next activation
                automation_state = "IDLE" # Reset state
                print("[Automation Thread] Automation loop reset to IDLE.")
        time.sleep(0.1) # Sleep briefly when automation is IDLE (to avoid busy-wait in infinite loop)


# --- Global variable for current motor speed, initialized to a default value ---
# This will be used to control the speed of the motors from the web interface
current_global_motor_speed = 50

@app.route('/')
def index():
    return render_template('index_g.html')

@app.route('/send_command', methods=['POST'])
def send_command():
    global automation_state, automation_active 
    data = request.get_json()
    command = data.get('command')
    print(f"Received command: {command}", flush=True)

    # If automation is active, ignore manual movement commands
    if automation_active.is_set(): 
        if command not in ['stop', 'start_automation', 'stop_automation']:
            print(f"[App] Ignoring manual command '{command}' while automation is active.")
            return jsonify({'status': 'ignored', 'message': 'Automation active'})

    # Handle automation start/stop commands sent from dashboard
    if command == 'start_automation':
        automation_active.set() # Set the event to start the automation thread
        print("[App] Automation sequence started via dashboard.")
        automation_state = "STARTED" # Update status
    elif command == 'stop_automation':
        automation_active.clear() # Clear the event to stop automation
        stop() # Immediately stop motors
        print("[App] Automation sequence stopped via dashboard.")
        automation_state = "STOPPED" # Update status
    else:

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


@app.route('/take_photo', methods=['POST'])
def take_photo():

    print("Received request to take photo.")

    with camera_frame_lock:
        frame_to_save = latest_camera_frame # Get the most recent frame

    if frame_to_save is None:
        print("ERROR: No frame available to take photo. Camera might not be streaming yet.")
        return jsonify({'status': 'error', 'message': 'No frame available'}), 500
    
    
    if not cam or not cam.isOpened():
        print("ERROR: Camera not open for taking photo.")
        return jsonify({'status': 'error', 'message': 'Camera not available'}), 500
    


    ret, frame = cam.read() 
    if not ret:
        print("ERROR: Failed to grab frame for photo.")
        return jsonify({'status': 'error', 'message': 'Failed to capture frame'}), 500
    
    # Define a folder to save captured photos
    # --- CHANGED: Now saves to the 'data/photos' subfolder ---
    PHOTO_SAVE_FOLDER = os.path.join(os.path.dirname(__file__), 'data', 'photos')
    os.makedirs(PHOTO_SAVE_FOLDER, exist_ok=True) 
    
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"photo_{timestamp}.jpg"
    filepath = os.path.join(PHOTO_SAVE_FOLDER, filename)
    
    try:
        cv2.imwrite(filepath, frame)
        print(f"Photo saved to: {filepath}")
        # --- CHANGED: Return path that uses the new /data_files route ---
        return jsonify({'status': 'success', 'filename': filename, 'path': f'/data_files/photos/{filename}'})
    except Exception as e:
        print(f"ERROR: Failed to save photo: {e}")
        return jsonify({'status': 'error', 'message': f'Failed to save photo: {e}'}), 500

    

# --- NEW: Route to serve files from the 'data' folder ---
@app.route('/data_files/<path:filename>')
def data_files(filename):
    # _DATA_FOLDER_GLOBAL = os.path.join(os.path.dirname(__file__), 'data') 
    
    return send_from_directory(DATA_FOLDER, filename)



@app.route("/mjpeg")
def mjpeg():
    return Response(gather_img(), mimetype='multipart/x-mixed-replace; boundary=frame')

# --- to get Odometry Pose ---
@app.route('/get_pose')
def get_pose():
    with encoder_data_lock: # Use the same lock as encoder data for consistency
        x, y, theta_deg = odometry.get_pose()
        absolute_distance = math.sqrt(x**2 + y**2) # Calculates distance from (0,0)
    return jsonify({'x': x, 
                    'y': y, 
                    'theta': theta_deg,
                    'distance': absolute_distance })
    

# ---  DELAY FOR CAMERA ---
# print("Delaying for camera warm-up...")
# time.sleep(5) # Wait 5 seconds to ensure camera is fully initialized

cam = cv2.VideoCapture(0)
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# qr_detector = cv2.QRCodeDetector()
# detected_qr_data = set()

def gather_img():
    # NEW: Global variable for the latest camera frame and a lock for thread safety ---
    global latest_camera_frame # Must be declared global if written to

    if not cam or not cam.isOpened():
        print("Error: Camera not open in gather_img. Cannot stream.")
        return 

    DISPLAY_CV2_WINDOW = False # Set to False if you DO NOT want the local window
    if DISPLAY_CV2_WINDOW:
        cv2.namedWindow("Local Camera Feed (via Flask)", cv2.WINDOW_AUTOSIZE)
        print("Local camera feed window opened.")

    while True:
        ret, frame = cam.read() 
        if not ret:
            print("Failed to grab frame. End of stream or camera error. Retrying frame...")
            time.sleep(0.5) 
            continue 
        
        processed_frame = qr(frame) 
        if processed_frame is None:
            processed_frame = frame

        # --- Store the latest frame securely ---
        with camera_frame_lock:
            latest_camera_frame = processed_frame.copy() # Store a copy of the latest frame

        if DISPLAY_CV2_WINDOW:
            cv2.imshow("Local Camera Feed (via Flask)", processed_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                print(" 'q' pressed in local window. Stopping local display for this request.")
                break 

        _, buffer = cv2.imencode('.jpg', processed_frame) 
        frame_encoded_bytes = buffer.tobytes()

        yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame_encoded_bytes + b'\r\r\n')

    if DISPLAY_CV2_WINDOW:
        cv2.destroyAllWindows()
        print("Local camera feed window closed.")


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
    if not cam or not cam.isOpened():
        print("Flask app will start, but camera is not available.")
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

