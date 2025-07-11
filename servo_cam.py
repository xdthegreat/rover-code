# servo_cam.py

import board
import busio
import adafruit_pca9685
import time

# --- PCA9685 I2C Setup ---
# Create the I2C bus object. On Raspberry Pi, the default I2C bus is typically 1.
# i2c = busio.I2C(board.SCL, board.SDA)

# # Create a PCA9685 object with its default I2C address (0x40)
# pca = adafruit_pca9685.PCA9685(i2c)

# # Set PWM frequency for servos (50 Hz is standard)
# pca.frequency = 50

# # --- Servo Configuration ---
# SERVO_CHANNEL = 3 # Connect your servo to Channel 3 on the PCA9685 board

# # These define the pulse width range for 0 to 180 degrees.
# # You might need to calibrate these values for your specific servo
# # 500us = ~0 degrees, 2500us = ~180 degrees (for a 20ms period, 50Hz)
# # The library's duty_cycle property expects a 16-bit value (0-65535)
# # This converts microseconds to the 0-65535 range for CircuitPython's PCA9685 library.
# min_pulse_value = int(500 * (65535 / 20000.0))  # 500us / 20ms * 65535
# max_pulse_value = int(2500 * (65535 / 20000.0)) # 2500us / 20ms * 65535

# # Helper function to map angle (0-180) to duty cycle value (min_pulse_value to max_pulse_value)
# def angle_to_duty_cycle(angle_degrees):
#     angle_degrees = max(0, min(180, angle_degrees))
#     # Interpolate the value between min_pulse_value and max_pulse_value
#     value = min_pulse_value + (angle_degrees / 180.0) * (max_pulse_value - min_pulse_value)
#     return int(value)

# # --- Main Test Loop ---
# if __name__ == "__main__":
#     try:
#         print(f"Testing PCA9685 servo on Channel {SERVO_CHANNEL} at 50Hz.")
#         print(f"Pulse range: {min_pulse_value} to {max_pulse_value} (0 to 180 degrees)")
        
#         # Test 0 degrees
#         print("Moving to 0 degrees...")
#         pca.channels[SERVO_CHANNEL].duty_cycle = angle_to_duty_cycle(0)
#         time.sleep(1.5)

#         # Test 90 degrees
#         print("Moving to 90 degrees...")
#         pca.channels[SERVO_CHANNEL].duty_cycle = angle_to_duty_cycle(90)
#         time.sleep(1.5)

#         # Test 180 degrees
#         print("Moving to 180 degrees...")
#         pca.channels[SERVO_CHANNEL].duty_cycle = angle_to_duty_cycle(180)
#         time.sleep(1.5)

#         # Test back to 90 degrees
#         print("Moving back to 90 degrees...")
#         pca.channels[SERVO_CHANNEL].duty_cycle = angle_to_duty_cycle(90)
#         time.sleep(1.5)

#     except KeyboardInterrupt:
#         print("\nTest interrupted by user.")
#     except Exception as e:
#         print(f"An error occurred: {e}")
#     finally:
#         print("Setting servo duty cycle to 0 (off) and cleaning up.")
#         # Turn off the servo signal completely to save power and prevent jitter
#         pca.channels[SERVO_CHANNEL].duty_cycle = 0 
#         # No GPIO.cleanup() needed for PCA9685 as it's I2C, not direct GPIO.
#         print("Test complete.")




# ###################################
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