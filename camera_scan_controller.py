# camera_scan.py (will contain the CameraScanController class)

import threading
import time
import math # Needed for angle calculations if you include custom servo math
# Assuming you have a global camera_servo_controller object available via app_instance.camera_servo_controller
# Or you pass it directly to the constructor if it's not a Flask app specific design.

class CameraScanController:
    def __init__(self, app_instance, camera_servo_controller_obj):
        """
        Initializes the CameraScanController.
        :param app_instance: The Flask app object, needed for app.app_context().
        :param camera_servo_controller_obj: The instantiated CameraServoController object.
        """
        self.app = app_instance
        self.camera_servo_controller = camera_servo_controller_obj

        # --- Camera Scan Configuration (now instance variables) ---
        self.scan_active = threading.Event() # Event to signal the thread to run/stop
        self.scan_min_angle = 45 # Degrees
        self.scan_max_angle = 135 # Degrees
        self.scan_step_angle = 5 # Degrees per step during scan
        self.scan_delay = 0.01 # Seconds delay between steps
        
        print("[CameraScanController] Initialized.")

        # Start the camera scan control thread
        self.scan_thread = threading.Thread(target=self._run_scan_loop, daemon=True)
        self.scan_thread.start()
        print("[CameraScanController] Camera scan control thread launched.")

    # --- Public Methods to Control Scan ---
    def start_scan(self):
        """Activates the camera scan thread to begin scanning."""
        if not self.scan_active.is_set(): # Only set if not already active
            self.scan_active.set()
            print("[CameraScanController] Camera scan activated.")
        else:
            print("[CameraScanController] Camera scan is already active. Ignoring start command.")

    def stop_scan(self):
        """Deactivates the camera scan thread and stops the current scan."""
        if self.scan_active.is_set(): # Only clear if active
            self.scan_active.clear()
            # Ensure servo returns to center and stops motion
            if self.camera_servo_controller:
                self.camera_servo_controller.set_angle(90) # Return to center
            print("[CameraScanController] Camera scan stopped.")
        else:
            print("[CameraScanController] Camera scan is already inactive. Ignoring stop command.")

    def is_scanning(self):
        """Returns True if camera is currently scanning, False otherwise."""
        return self.scan_active.is_set()

    # --- Internal Scan Control Loop (runs in its own thread) ---
    def _run_scan_loop(self):
        print("[CameraScanController Thread] Camera scan control loop running in background...")
        
        current_scan_angle = 90 # Start scan from center (default position)
        scan_direction_up = True # True for increasing angle, False for decreasing

        while True:
            self.scan_active.wait() # Block until self.scan_active.set() is called

            print(f"[CameraScanController Thread] Scan activated. Scanning from {self.scan_min_angle}° to {self.scan_max_angle}°")
            
            with self.app.app_context(): # Ensure Flask context for logging, or if calling Flask globals
                try:
                    while self.scan_active.is_set(): # Continue scanning until scan_active.clear() is called
                        # Determine next angle based on direction
                        if scan_direction_up:
                            current_scan_angle += self.scan_step_angle
                            if current_scan_angle > self.scan_max_angle:
                                current_scan_angle = self.scan_max_angle # Clamp at max
                                scan_direction_up = False # Change direction
                        else:
                            current_scan_angle -= self.scan_step_angle
                            if current_scan_angle < self.scan_min_angle:
                                current_scan_angle = self.scan_min_angle # Clamp at min
                                scan_direction_up = True # Change direction
                        
                        # Command the servo to the new angle
                        if self.camera_servo_controller:
                            self.camera_servo_controller.set_angle(current_scan_angle)
                        
                        time.sleep(self.scan_delay) # Delay between steps
                
                except Exception as e:
                    print(f"[CameraScanController Thread] CRITICAL ERROR in camera scan loop: {e}")
                    if self.camera_servo_controller:
                        self.camera_servo_controller.set_angle(90) # Return to center on error
                finally:
                    self.scan_active.clear() # Clear the event for next activation
                    self.current_state = "IDLE" # Reset state
                    print("[CameraScanController Thread] Camera scan loop reset to IDLE (waiting for next scan).")
            time.sleep(0.1) # Sleep briefly when scan is IDLE

    def cleanup(self):
        """Ensure the scan thread is stopped and servo is reset on app shutdown."""
        self.stop_scan() # Ensure thread event is cleared
        if self.camera_servo_controller:
            self.camera_servo_controller.set_angle(90) # Return to center
        # No specific thread.join() needed here if it's a daemon thread and app is exiting.
        print("[CameraScanController] Cleanup complete.")