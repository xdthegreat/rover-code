import serial
import time

# On Raspberry Pi, adjust this to match your Arduino's serial device:
# - /dev/ttyUSB0 if connected via USB cable
# - /dev/serial0 or /dev/ttyAMA0 if using the Pi’s GPIO UART
SERIAL_PORT = "/dev/ttyACM0"  
BAUD_RATE = 115200

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
    except serial.SerialException as e:
        print(f"Failed to open serial port {SERIAL_PORT}: {e}")
        return

    time.sleep(2)  # Let Arduino reset after serial connection

    print(f"Reading encoder data from Arduino on {SERIAL_PORT}...\n")
    try:
        while True:
            line = ser.readline().decode("utf-8", errors="ignore").strip()
            if not line:
                continue  # Skip empty lines

            parts = line.split(",")
            if len(parts) != 7:
                print(f"Invalid line: {line}")
                continue

            try:
                rpm1 = float(parts[3])
                speed1 = float(parts[4])
                rpm2 = float(parts[5])
                speed2 = float(parts[6])
            except ValueError:
                print(f"Parse error: {line}")
                continue

            print(f"ENC1 → RPM: {rpm1:.2f}, Speed: {speed1:.2f} cm/s | "
                  f"ENC2 → RPM: {rpm2:.2f}, Speed: {speed2:.2f} cm/s")

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        ser.close()

if __name__ == "__main__":
    main()