# serial_comm.py
import serial
import time

class ArduinoSerialComm:
    def __init__(self, port, baud_rate):
        self.ser = None # Initialize to None
        try:
            # Open the serial port with a timeout
            self.ser = serial.Serial(port, baud_rate, timeout=1) 
            print(f"Serial connected to Arduino at {port} at {baud_rate} baud.")
            time.sleep(2) # Give the serial port time to initialize and Arduino to reset
            # Read any initial messages from Arduino after connection
            while self.ser.in_waiting > 0:
                print(f"Arduino init message: {self.ser.readline().decode().strip()}")
        except serial.SerialException as e:
            # Print a user-friendly error message if connection fails
            print(f"ERROR: Could not open serial port {port}: {e}")
            print(f"Please check: 1. Is Osoyoo Mega connected? 2. Is {port} correct? 3. Are permissions set (sudo usermod -a -G dialout $USER and reboot)?")
            self.ser = None # Ensure ser is None if connection fails

    def send_command(self, command_str):
        # Check if serial port is open before attempting to write
        if self.ser and self.ser.is_open:
            try:
                # Encode the string command to bytes and add a newline character
                self.ser.write((command_str.strip() + '\n').encode('utf-8'))
                print(f"Sent to Arduino: '{command_str.strip()}'")
            except serial.SerialException as e:
                print(f"Error writing to serial: {e}")
        else:
            print("Serial port not open. Cannot send command to Arduino.")

    def read_data(self):
        # Check if serial port is open before attempting to read
        if self.ser and self.ser.is_open:
            try:
                if self.ser.in_waiting > 0: # Check if there's data waiting to be read
                    line = self.ser.readline().decode('utf-8').strip() # Read line, decode to string, remove whitespace
                    # print(f"Received from Arduino: {line}") # Uncomment for debugging received data
                    return line
            except serial.SerialException as e:
                print(f"Error reading from serial: {e}")
        return None # Return None if no data or error

    def close(self):
        # Close the serial port if it's open
        if self.ser and self.ser.is_open:
            self.ser.close()
            print("Serial connection to Arduino closed.")