# # hardware.py - Raspberry Pi Rover Motor Control Script
# # This script controls the motors of a rover using GPIO pins on Raspberry Pi.

# # import RPi.GPIO as GPIO
# from gpiozero import PWMOutputDevice, DigitalOutputDevice
# import time

# PWM1 = 17 #white
# DIR1 = 18 #black (Left Motor)
# PWM2 = 22 #purple
# DIR2 = 23 #gray (Right Motor)


# GPIO.setmode(GPIO.BCM)
# GPIO.setwarnings(False) 

# GPIO.setup([PWM1, DIR1, PWM2, DIR2], GPIO.OUT)

# pwm1 = GPIO.PWM(PWM1, 1000) #Left PWM
# pwm2 = GPIO.PWM(PWM2, 1000) #Right PWM

# pwm1.start(0)
# pwm2.start(0)

# def forward(speed):
#     """Moves the rover straight forward.
#        Speed is 0-100.
#        IMPORTANT: DIR1's logic is inverted compared to previous version.
#     """
#     print(f"[Hardware] Moving forward at {speed}% speed")
#     # If DIR1=LOW was perceived as BACKWARD, now DIR1=HIGH will be FORWARD.
#     GPIO.output(DIR1, GPIO.HIGH) # <--- CHANGED: Inverted DIR1 from LOW to HIGH
#     GPIO.output(DIR2, GPIO.LOW)  # Right motor forward (remains LOW)
#     pwm1.ChangeDutyCycle(speed)
#     pwm2.ChangeDutyCycle(speed)

# def backward(speed):
#     """Moves the rover straight backward.
#        Speed is 0-100.
#        IMPORTANT: DIR1's logic is inverted compared to previous version.
#     """
#     print(f"[Hardware] Moving backward at {speed}% speed")
#     # If DIR1=HIGH was perceived as FORWARD, now DIR1=LOW will be BACKWARD.
#     GPIO.output(DIR1, GPIO.LOW)  # <--- CHANGED: Inverted DIR1 from HIGH to LOW
#     GPIO.output(DIR2, GPIO.HIGH) # Right motor backward (remains HIGH)
#     pwm1.ChangeDutyCycle(speed)
#     pwm2.ChangeDutyCycle(speed)

# def turn_left(speed):
#     """Turns the rover left (left wheels backward, right wheels forward).
#        Speed is 0-100.
#        Logic adjusted based on new DIR1 mapping.
#     """
#     print(f"[Hardware] Turning left at {speed}% speed")
#     # Left motor backward (now needs LOW for DIR1)
#     GPIO.output(DIR1, GPIO.HIGH)  # <--- CHANGED: Inverted DIR1 from HIGH to LOW
#     GPIO.output(DIR2, GPIO.HIGH)  # Right motor forward (remains LOW)
#     pwm1.ChangeDutyCycle(speed)
#     pwm2.ChangeDutyCycle(speed)

# def turn_right(speed):
#     """Turns the rover right (left wheels forward, right wheels backward).
#        Speed is 0-100.
#        Logic adjusted based on new DIR1 mapping.
#     """
#     print(f"[Hardware] Turning right at {speed}% speed")
#     # Left motor forward (now needs HIGH for DIR1)
#     GPIO.output(DIR1, GPIO.LOW) # <--- CHANGED: Inverted DIR1 from LOW to HIGH
#     GPIO.output(DIR2, GPIO.LOW) # Right motor backward (remains HIGH)
#     pwm1.ChangeDutyCycle(speed)
#     pwm2.ChangeDutyCycle(speed)

# def stop():
#     """Stops all motors (sets PWM duty cycle to 0)."""
#     print("[Hardware] Stopping motors")
#     pwm1.ChangeDutyCycle(0)
#     pwm2.ChangeDutyCycle(0)
#     # Reset DIR pins to a consistent state (e.g., what is now "forward" for both sides)
#     GPIO.output(DIR1, GPIO.HIGH) # <--- CHANGED: To match new "forward" default for DIR1
#     GPIO.output(DIR2, GPIO.LOW)  # <--- CHANGED: To match new "forward" default for DIR2
    
# def cleanup_gpio():
#     """Cleans up GPIO resources."""
#     print("[Hardware] Cleaning up GPIO...")
#     pwm1.stop()
#     pwm2.stop()
#     GPIO.cleanup()
#     print("Hardware GPIO cleanup complete.")

# # --- Example Usage (for testing this file independently) ---
# if __name__ == '__main__':
#     try:
#         print("Testing hardware.py motor control...")
        
#         print("\n--- Testing Forward ---")
#         forward(50) 
#         time.sleep(2)
#         stop()
#         time.sleep(1)

#         print("\n--- Testing Backward ---")
#         backward(40)
#         time.sleep(2)
#         stop()
#         time.sleep(1)

#         print("\n--- Testing Turn Left (Spin in Place) ---")
#         turn_left(60)
#         time.sleep(1.5)
#         stop()
#         time.sleep(1)

#         print("\n--- Testing Turn Right (Spin in Place) ---")
#         turn_right(60)
#         time.sleep(1.5)
#         stop()
#         time.sleep(1)

#     except KeyboardInterrupt:
#         print("\nTest interrupted.")
#     finally:
#         cleanup_gpio()


# hardware.py (Refactored to use gpiozero for motors, PCA9685 for servo cam)

# --- CHANGED: Use gpiozero instead of RPi.GPIO ---
from gpiozero import PWMOutputDevice, DigitalOutputDevice
import time

# --- PCA9685 Imports (for servo cam only) ---
import board
import busio
import adafruit_pca9685


# --- Motor Pin Definitions (gpiozero uses BCM numbering directly) ---
PWM1 = 17 # Left Motor PWM (BCM GPIO 17)
DIR1 = 18 # Left Motor Direction (BCM GPIO 18)
PWM2 = 22 # Right Motor PWM (BCM GPIO 22)
DIR2 = 23 # Right Motor Direction (BCM GPIO 23)

# --- Camera Tilt Servo PCA9685 Configuration ---
SERVO_CAM_PCA_ADDRESS = 0x40 # Adjust to your servo's PCA9685 board's I2C address!
CAMERA_TILT_SERVO_CHANNEL = 3 # Servo connected to PCA9685 Channel 3 (Port 3)

# --- Servo Pulse Range Calibration for set_camera_tilt_angle ---
SERVO_MIN_PULSE_VALUE = int(500 * (65535 / 20000.0))
SERVO_MAX_PULSE_VALUE = int(2500 * (65535 / 20000.0))


# --- gpiozero Setup (for Motors) ---
# Initialize PWM for motors using PWMOutputDevice
pwm1_motor = PWMOutputDevice(PWM1, frequency=1000) # Left Motor PWM object
pwm2_motor = PWMOutputDevice(PWM2, frequency=1000) # Right Motor PWM object

# Initialize DigitalOutputDevice for direction pins
dir1_pin = DigitalOutputDevice(DIR1) # Left Motor Direction pin
dir2_pin = DigitalOutputDevice(DIR2) # Right Motor Direction pin


# --- PCA9685 I2C and Object Setup (for Servo Cam PCA ONLY) ---
i2c = busio.I2C(board.SCL, board.SDA) 
servo_cam_pca = adafruit_pca9685.PCA9685(i2c, address=SERVO_CAM_PCA_ADDRESS)
servo_cam_pca.frequency = 50 


# --- Motor Control Functions (using gpiozero) ---

def forward(speed):
    """Moves the rover straight forward. Speed is 0-100."""
    print(f"[Hardware] Moving forward at {speed}% speed (via gpiozero)")
    # Set direction pins (False for LOW, True for HIGH) - VERIFY THIS LOGIC ON YOUR ROBOT
    dir1_pin.on() # Left Motor Direction (adjust on()/off() based on testing)
    dir2_pin.off() # Right Motor Direction (adjust on()/off() based on testing)
    # Set PWM speed (0.0 to 1.0 for gpiozero)
    pwm1_motor.value = speed / 100.0
    pwm2_motor.value = speed / 100.0

def backward(speed):
    """Moves the rover straight backward. Speed is 0-100."""
    print(f"[Hardware] Moving backward at {speed}% speed (via gpiozero)")
    dir1_pin.off() # Left Motor Direction
    dir2_pin.on() # Right Motor Direction
    pwm1_motor.value = speed / 100.0
    pwm2_motor.value = speed / 100.0

def turn_left(speed):
    """Turns the rover left (left wheels backward, right wheels forward). Speed is 0-100."""
    print(f"[Hardware] Turning left at {speed}% speed (via gpiozero)")
    dir1_pin.off()  # Left motor backward
    dir2_pin.off() # Right motor forward
    pwm1_motor.value = speed / 100.0
    pwm2_motor.value = speed / 100.0

def turn_right(speed):
    """Turns the rover right (left wheels forward, right wheels backward). Speed is 0-100."""
    print(f"[Hardware] Turning right at {speed}% speed (via gpiozero)")
    dir1_pin.on() # Left motor forward
    dir2_pin.on()  # Right motor backward
    pwm1_motor.value = speed / 100.0
    pwm2_motor.value = speed / 100.0

def stop():
    """Stops all motors (sets PWM duty cycle to 0)."""
    print("[Hardware] Stopping motors (via gpiozero)")
    pwm1_motor.value = 0.0 # 0% duty cycle
    pwm2_motor.value = 0.0 # 0% duty cycle
    # Reset direction pins to a consistent state
    dir1_pin.off() 
    dir2_pin.off() 

# --- Camera Tilt Servo Control Function (using SERVO_CAM_PCA) ---
def set_camera_tilt_angle(angle_degrees):
    """Sets the tilt angle of the camera servo on SERVO_CAM_PCA.
       Angle: 0 to 180 degrees. Uses calibrated min/max pulse values.
    """
    angle_degrees = max(0, min(180, angle_degrees))
    value = SERVO_MIN_PULSE_VALUE + (angle_degrees / 180.0) * (SERVO_MAX_PULSE_VALUE - SERVO_MIN_PULSE_VALUE)
    servo_cam_pca.channels[CAMERA_TILT_SERVO_CHANNEL].duty_cycle = int(value)
    print(f"[Hardware] Camera tilt set to {angle_degrees} degrees (PCA9685 Channel {CAMERA_TILT_SERVO_CHANNEL})")
    time.sleep(0.1) # Give servo time to move (adjust as needed)


# --- Cleanup Function ---

def cleanup_gpio(): # This function cleans up gpiozero (motors) and PCA9685 (servo) resources.
    """Cleans up gpiozero (motors) and PCA9685 (servo) resources."""
    print("[Hardware] Performing cleanup...")
    # gpiozero Cleanup (for motors)
    pwm1_motor.close() # Close gpiozero devices
    pwm2_motor.close()
    dir1_pin.close()
    dir2_pin.close()

    # PCA9685 Servo Cleanup
    servo_cam_pca.channels[CAMERA_TILT_SERVO_CHANNEL].duty_cycle = 0 
    
    print("Hardware cleanup complete.")


# --- Example Usage (for testing this hardware.py independently) ---
if __name__ == '__main__':
    try:
        print("--- Testing Camera Tilt Servo (PCA9685 Channel 3) ---")
        set_camera_tilt_angle(0)   # 0 degrees
        time.sleep(1.5)
        set_camera_tilt_angle(90)  # 90 degrees (center)
        time.sleep(1.5)
        set_camera_tilt_angle(180) # 180 degrees
        time.sleep(1.5)
        set_camera_tilt_angle(90)  # Back to center
        time.sleep(1.5)
        
        print("\n--- Testing gpiozero Motor Controls ---")
        forward(50) # 50% speed
        time.sleep(2)
        stop()
        time.sleep(1)

        backward(40)
        time.sleep(2)
        stop()
        time.sleep(1)

        turn_left(60)
        time.sleep(1.5)
        stop()
        time.sleep(1)

        turn_right(60)
        time.sleep(1.5)
        stop()
        time.sleep(1)

    except KeyboardInterrupt:
        print("\nTest interrupted.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        cleanup_gpio()