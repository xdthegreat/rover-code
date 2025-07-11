# import board        # From adafruit-blinka
# import busio        # From adafruit-blinka (for I2C, not directly used here but common)
# import RPi.GPIO as GPIO

# import adafruit_bno08x
# from adafruit_bno08x.uart import BNO08X_UART

# import serial
# uart = serial.Serial("/dev/serial0", 115200)

# bno = BNO08X_UART(uart)

# import time

# while True:
#     if bno.data_ready:
#         event = bno.read()
#         if event and event.orientation:
#             print("Yaw: {:.2f}, Pitch: {:.2f}, Roll: {:.2f}".format(
#                 event.orientation.yaw,
#                 event.orientation.pitch,
#                 event.orientation.roll
#             ))
#     time.sleep(0.01)
    
    
# bno08x_test.py

import board        # From adafruit-blinka
import busio        # From adafruit-blinka (for I2C, not directly used here but common)
import RPi.GPIO as GPIO # For controlling reset/interrupt pins if not using board.DXX

import adafruit_bno08x
from adafruit_bno08x.uart import BNO08X_UART

import serial       # For pyserial
import time

# --- Configure UART Serial Port ---
# This matches the /dev/serial0 setup on Raspberry Pi
uart = serial.Serial("/dev/serial0", 115200)

# --- Configure BNO08x Pins ---
# Using BCM GPIO numbers for reset/interrupt pins
# These map to the physical pins connected to BNO08x RST and INT
BNO_RESET_PIN = board.D17 # GPIO17, Physical Pin 11
BNO_INT_PIN = board.D27   # GPIO27, Physical Pin 13

# --- Initialize BNO08x Sensor ---
# Pass the UART object and the reset/interrupt pins
try:
    bno = BNO08X_UART(uart, BNO_RESET_PIN, BNO_INT_PIN)
    print("BNO08x sensor initialized.")
except Exception as e:
    print(f"CRITICAL ERROR: Failed to initialize BNO08x sensor: {e}")
    print("Please check wiring (VCC, GND, TX, RX, RST, INT), UART config in raspi-config, and permissions.")
    exit() # Exit if sensor fails to initialize

# --- Enable Sensor Reports (Choose the reports you need) ---
# For orientation, enable Rotation Vector
bno.enable_feature(adafruit_bno08x.BNO_REPORT_ROTATION_VECTOR)
# You can enable other features as needed:
# bno.enable_feature(adafruit_bno08x.BNO_REPORT_GEOMAGNETIC_ROTATION_VECTOR)
# bno.enable_feature(adafruit_bno08x.BNO_REPORT_ACCELEROMETER)
# bno.enable_feature(adafruit_bno08x.BNO_REPORT_GYROSCOPE)
# bno.enable_feature(adafruit_bno08x.BNO_REPORT_LINEAR_ACCELERATION)
# bno.enable_feature(adafruit_bno08x.BNO_REPORT_GRAVITY)

# --- Main Loop to Read Data ---
print("Reading BNO08x data (Ctrl+C to quit)...")
try:
    while True:
        if bno.data_ready: # Check if new data is available
            event = bno.read() # Read the event data
            
            # Check if the event contains orientation data
            if event and event.orientation:
                print("Yaw: {:.2f}, Pitch: {:.2f}, Roll: {:.2f}".format(
                    event.orientation.yaw,
                    event.orientation.pitch,
                    event.orientation.roll
                ))
            # You can add checks for other data types if you enable them
            # elif event and event.acceleration:
            #     print(f"Accel X:{event.acceleration.x:.2f}, Y:{event.acceleration.y:.2f}, Z:{event.acceleration.z:.2f}")

        time.sleep(0.01) # Small delay to prevent busy-looping

except KeyboardInterrupt:
    print("\nScript interrupted by user.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")
finally:
    # --- Cleanup ---
    print("Cleaning up serial connection.")
    uart.close() # Close the serial port
    print("Cleanup complete.")


if __name__ == "__main__":
    main()