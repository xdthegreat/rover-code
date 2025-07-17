# servo_cam.py

import board
import busio
import adafruit_pca9685
import time

# --- Camera Tilt Servo PCA9685 Configuration ---
# IMPORTANT: Adjust to your servo's PCA9685 board's I2C address!
SERVO_CAM_PCA_ADDRESS = 0x40 # Example: Address for the PCA9685 controlling the camera servo

# PCA9685 Channel for the Camera Tilt Servo
CAMERA_TILT_SERVO_CHANNEL = 3 # Example: Connect Camera Tilt Servo Signal to Channel 0 of this PCA9685

# --- Servo Pulse Range Calibration ---
SERVO_MIN_PULSE_VALUE = int(500 * (65535 / 20000.0))  # ~1638 for 0 degrees
SERVO_MAX_PULSE_VALUE = int(2500 * (65535 / 20000.0)) # ~8192 for 180 degrees


class CameraServoController:
    def __init__(self, i2c_bus, pca_address, servo_channel):
        self.pca = None
        self.servo_channel = servo_channel

        try:
            # Create PCA9685 object for the camera servo board
            self.pca = adafruit_pca9685.PCA9685(i2c_bus, address=pca_address)
            self.pca.frequency = 50 # Set PWM frequency to 50 Hz
            print(f"[CameraServo] Initialized PCA9685 at 0x{pca_address:X} for channel {servo_channel}")
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to initialize Camera Servo PCA9685 at 0x{pca_address:X}: {e}")
            self.pca = None

    def set_angle(self, angle_degrees):
        """Sets the tilt angle of the camera servo.
           Angle: 0 to 180 degrees. Uses calibrated min/max pulse values.
        """
        if self.pca is None:
            print("[CameraServo] ERROR: PCA9685 not initialized. Cannot set angle.")
            return

        angle_degrees = max(0, min(180, angle_degrees))
        
        # Map angle (0-180) to duty cycle value (SERVO_MIN_PULSE_VALUE to SERVO_MAX_PULSE_VALUE)
        value = SERVO_MIN_PULSE_VALUE + (angle_degrees / 180.0) * (SERVO_MAX_PULSE_VALUE - SERVO_MIN_PULSE_VALUE)
        
        # Set the servo's PWM duty cycle on its assigned channel
        self.pca.channels[self.servo_channel].duty_cycle = int(value)
        print(f"[CameraServo] Tilt set to {angle_degrees} degrees (Channel {self.servo_channel})")
        time.sleep(0.1) # Give servo time to move (adjust as needed)

    def cleanup(self):
        """Turns off the servo signal."""
        if self.pca:
            self.pca.channels[self.servo_channel].duty_cycle = 0 # Turn off servo signal
            print(f"[CameraServo] Channel {self.servo_channel} signal turned off.")

# --- Example Usage (for testing this file independently) ---
if __name__ == "__main__":
    # This block requires I2C to be enabled and PCA9685 connected at 0x41 (or 0x40 if no motor board)
    print("Running independent Camera Servo Test...")
    
    # Initialize I2C bus here for independent test
    try:
        i2c_test_bus = busio.I2C(board.SCL, board.SDA)
        servo_controller_test = CameraServoController(i2c_test_bus, 0x41, 0) # Adjust address and channel for test
        
        if servo_controller_test.pca: # Check if PCA initialized successfully
            print("\n--- Testing Camera Tilt Servo ---")
            servo_controller_test.set_angle(0)   # 0 degrees
            time.sleep(1.5)
            servo_controller_test.set_angle(90)  # 90 degrees (center)
            time.sleep(1.5)
            servo_controller_test.set_angle(180) # 180 degrees
            time.sleep(1.5)
            servo_controller_test.set_angle(90)  # Back to center
            time.sleep(1.5)
        else:
            print("PCA9685 for servo cam not found/initialized. Skipping independent servo test.")

    except KeyboardInterrupt:
        print("\nTest interrupted by user.")
    except Exception as e:
        print(f"An error occurred during independent test: {e}")
    finally:
        if 'servo_controller_test' in locals():
            servo_controller_test.cleanup()
        print("Independent Camera Servo Test complete.")