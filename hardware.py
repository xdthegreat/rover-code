# hardware.py (Corrected - Inverting DIR1 logic based on observed behavior)

import RPi.GPIO as GPIO
import time

PWM1 = 17 #white
DIR1 = 18 #black (Left Motor)
PWM2 = 22 #purple
DIR2 = 23 #gray (Right Motor)

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False) 

GPIO.setup([PWM1, DIR1, PWM2, DIR2], GPIO.OUT)

pwm1 = GPIO.PWM(PWM1, 1000) #Left PWM
pwm2 = GPIO.PWM(PWM2, 1000) #Right PWM

pwm1.start(0)
pwm2.start(0)

def forward(speed):
    """Moves the rover straight forward.
       Speed is 0-100.
       IMPORTANT: DIR1's logic is inverted compared to previous version.
    """
    print(f"[Hardware] Moving forward at {speed}% speed")
    # If DIR1=LOW was perceived as BACKWARD, now DIR1=HIGH will be FORWARD.
    GPIO.output(DIR1, GPIO.HIGH) # <--- CHANGED: Inverted DIR1 from LOW to HIGH
    GPIO.output(DIR2, GPIO.LOW)  # Right motor forward (remains LOW)
    pwm1.ChangeDutyCycle(speed)
    pwm2.ChangeDutyCycle(speed)

def backward(speed):
    """Moves the rover straight backward.
       Speed is 0-100.
       IMPORTANT: DIR1's logic is inverted compared to previous version.
    """
    print(f"[Hardware] Moving backward at {speed}% speed")
    # If DIR1=HIGH was perceived as FORWARD, now DIR1=LOW will be BACKWARD.
    GPIO.output(DIR1, GPIO.LOW)  # <--- CHANGED: Inverted DIR1 from HIGH to LOW
    GPIO.output(DIR2, GPIO.HIGH) # Right motor backward (remains HIGH)
    pwm1.ChangeDutyCycle(speed)
    pwm2.ChangeDutyCycle(speed)

def turn_left(speed):
    """Turns the rover left (left wheels backward, right wheels forward).
       Speed is 0-100.
       Logic adjusted based on new DIR1 mapping.
    """
    print(f"[Hardware] Turning left at {speed}% speed")
    # Left motor backward (now needs LOW for DIR1)
    GPIO.output(DIR1, GPIO.LOW)  # <--- CHANGED: Inverted DIR1 from HIGH to LOW
    GPIO.output(DIR2, GPIO.LOW)  # Right motor forward (remains LOW)
    pwm1.ChangeDutyCycle(speed)
    pwm2.ChangeDutyCycle(speed)

def turn_right(speed):
    """Turns the rover right (left wheels forward, right wheels backward).
       Speed is 0-100.
       Logic adjusted based on new DIR1 mapping.
    """
    print(f"[Hardware] Turning right at {speed}% speed")
    # Left motor forward (now needs HIGH for DIR1)
    GPIO.output(DIR1, GPIO.HIGH) # <--- CHANGED: Inverted DIR1 from LOW to HIGH
    GPIO.output(DIR2, GPIO.HIGH) # Right motor backward (remains HIGH)
    pwm1.ChangeDutyCycle(speed)
    pwm2.ChangeDutyCycle(speed)

def stop():
    """Stops all motors (sets PWM duty cycle to 0)."""
    print("[Hardware] Stopping motors")
    pwm1.ChangeDutyCycle(0)
    pwm2.ChangeDutyCycle(0)
    # Reset DIR pins to a consistent state (e.g., what is now "forward" for both sides)
    GPIO.output(DIR1, GPIO.HIGH) # <--- CHANGED: To match new "forward" default for DIR1
    GPIO.output(DIR2, GPIO.LOW)  # <--- CHANGED: To match new "forward" default for DIR2
    
def cleanup_gpio():
    """Cleans up GPIO resources."""
    print("[Hardware] Cleaning up GPIO...")
    pwm1.stop()
    pwm2.stop()
    GPIO.cleanup()
    print("Hardware GPIO cleanup complete.")

# --- Example Usage (for testing this file independently) ---
if __name__ == '__main__':
    try:
        print("Testing hardware.py motor control...")
        
        print("\n--- Testing Forward ---")
        forward(50) 
        time.sleep(2)
        stop()
        time.sleep(1)

        print("\n--- Testing Backward ---")
        backward(40)
        time.sleep(2)
        stop()
        time.sleep(1)

        print("\n--- Testing Turn Left (Spin in Place) ---")
        turn_left(60)
        time.sleep(1.5)
        stop()
        time.sleep(1)

        print("\n--- Testing Turn Right (Spin in Place) ---")
        turn_right(60)
        time.sleep(1.5)
        stop()
        time.sleep(1)

    except KeyboardInterrupt:
        print("\nTest interrupted.")
    finally:
        cleanup_gpio()