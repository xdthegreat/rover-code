#  automation_controller.py 

import threading
import time
import math

class AutomationController:
    def __init__(self, app_instance, odometry_obj, encoder_lock, hardware_motor_funcs):
        """
        Initializes the AutomationController.
        :param app_instance: The Flask app object, needed for app.app_context().
        :param odometry_obj: The global SkidSteerOdometry object.
        :param encoder_lock: The threading.Lock for accessing odometry/encoder data.
        :param hardware_motor_funcs: A dictionary or object containing motor control functions (forward, backward, turn_left, turn_right, stop).
        """
        self.app = app_instance
        self.odometry = odometry_obj
        self.encoder_data_lock = encoder_lock
        self.motor_funcs = hardware_motor_funcs # e.g., {'forward': forward, 'stop': stop}

        self.automation_active = threading.Event() # Event to signal the thread to run/wait
        self.automation_target_distance = 0.0 # meters
        self.automation_target_direction = 0.0 # degrees
        self.automation_speed = 30 # Default speed for automation (in %)
        self.automation_state = "IDLE" # States: IDLE, TURNING, DRIVING, FINISHED, STOPPED

        print("[AutomationController] Initialized.")

    def set_mission_targets(self, distance, direction):
        """Sets the new target distance and direction for the autonomous mission."""
        self.automation_target_distance = distance
        self.automation_target_direction = direction
        print(f"[AutomationController] Targets set: Distance={distance}m, Direction={direction}°")

    def start_mission(self):
        """Activates the automation thread to begin the mission."""
        if not self.automation_active.is_set(): # Only set if not already active
            self.automation_active.set()
            self.automation_state = "STARTED"
            print("[AutomationController] Mission started.")
        else:
            print("[AutomationController] Mission already active. Ignoring start command.")

    def stop_mission(self):
        """Deactivates the automation thread and stops the current mission."""
        if self.automation_active.is_set(): # Only clear if active
            self.automation_active.clear()
            # Immediately stop motors using the provided function
            self.motor_funcs['stop']() 
            self.automation_state = "STOPPED"
            print("[AutomationController] Mission stopped.")
        else:
            print("[AutomationController] Mission already inactive. Ignoring stop command.")


    def run_automation_thread(self):
        """
        This is the main loop for the automation thread.
        It runs continuously in the background, executing missions when activated.
        """
        print("[AutomationController Thread] Automation control loop started.")

        while True: # This loop runs continuously
            # Phase: IDLE - Waiting for Activation
            self.automation_active.wait() # Blocks until self.automation_active.set() is called

            print(f"[AutomationController Thread] Automation activated. Target Distance: {self.automation_target_distance}m, Target Direction: {self.automation_target_direction}°")
            
            # All actions within the automation sequence need to be within an app context
            with self.app.app_context(): 
                try:
                    # --- Get initial pose for distance calculation ---
                    with self.encoder_data_lock: # Safely access shared odometry data
                        initial_x, initial_y, initial_theta_deg = self.odometry.get_pose()

                    print(f"[AutomationController Thread] Mission Start Pose: X:{initial_x:.3f}, Y:{initial_y:.3f}, Theta:{initial_theta_deg:.1f}°") # NEW PRINT
                    
                    
 # --- Step 1: Turn to Target Direction ---
                    self.automation_state = "TURNING"
                    print(f"[AutomationController Thread] State: {self.automation_state}. Current Theta: {initial_theta_deg:.1f}°, Target: {self.automation_target_direction}°")
                    
                    angle_tolerance = 2.0 # Degrees +/- for alignment
                    turn_speed = self.automation_speed # Use the instance's automation speed

                    turn_count = 0 # NEW: counter for debug
                    
                    # Turn loop: continues until aligned or automation is stopped
                    while self.automation_active.is_set(): 
                        with self.encoder_data_lock: 
                            current_x, current_y, current_theta_deg = self.odometry.get_pose()
                        
                        angle_error = self.automation_target_direction - current_theta_deg
                        angle_error = self.odometry.normalize_angle_deg(angle_error) # Normalize error to -180 to 180

                        if turn_count % 10 == 0: # Print every 10 iterations (0.5s) to avoid spam
                            print(f"[AutomationController Thread] Turn Error: {angle_error:.1f}°, Current: {current_theta_deg:.1f}°")
                        turn_count += 1

                        if abs(angle_error) <= angle_tolerance:
                            print(f"[AutomationController Thread] Angle aligned. Current: {current_theta_deg:.1f}°")
                            self.motor_funcs['stop']() 
                            break # Exit turning loop
                        
                        if angle_error > 0: # Positive error: target is to the left
                            self.motor_funcs['turn_left'](turn_speed)
                        else: # Negative error: target is to the right
                            self.motor_funcs['turn_right'](turn_speed)
                        
                        time.sleep(0.05) 

                    # Check if automation was stopped during the turning phase
                    if not self.automation_active.is_set(): 
                        self.motor_funcs['stop']() 
                        self.automation_state = "IDLE"
                        print("[AutomationController Thread] Automation stopped during turn.")
                        continue # Go back to waiting for next activation


# --- Step 2: Drive to Target Distance ---
                    self.automation_state = "DRIVING"
                    print(f"[AutomationController Thread] State: {self.automation_state}. Target Distance: {self.automation_target_distance}m")
                    drive_speed = self.automation_speed 
                    distance_driving_tolerance = 0.05 # Meters, how close to target distance to stop (e.g., 5cm)

                    drive_count = 0 # NEW: counter for debug

                    # Driving loop: continues until distance reached or automation stopped
                    while self.automation_active.is_set(): 
                        with self.encoder_data_lock: 
                            current_x, current_y, current_theta_deg = self.odometry.get_pose()
                        
                        distance_traveled = math.sqrt((current_x - initial_x)**2 + (current_y - initial_y)**2)
                        distance_remaining = self.automation_target_distance - distance_traveled

                        if drive_count % 10 == 0: # Print every 10 iterations (0.5s)
                            print(f"[AutomationController Thread] Drive Remaining: {distance_remaining:.2f}m, Traveled: {distance_traveled:.2f}m")
                        drive_count += 1

                        if distance_remaining <= distance_driving_tolerance: 
                            print(f"[AutomationController Thread] Distance reached. Traveled: {distance_traveled:.2f}m")
                            self.motor_funcs['stop']() 
                            break # Exit driving loop
                        
                        self.motor_funcs['forward'](drive_speed) 
                        print(f"[AutomationController Thread] Driving, remaining: {distance_remaining:.2f}m") # Uncomment for verbose driving debug
                        time.sleep(0.05) 

                    # Check if automation was stopped during the driving phase
                    if not self.automation_active.is_set(): 
                        self.motor_funcs['stop']() 
                        self.automation_state = "IDLE"
                        print("[AutomationController Thread] Automation stopped during drive.")
                        continue # Go back to waiting for next activation


# --- Step 3: Mission Finished ---
                    self.automation_state = "FINISHED"
                    self.motor_funcs['stop']() 
                    print("[AutomationController Thread] Automation sequence completed.")
                    
                except Exception as e:
                    print(f"[AutomationController Thread] CRITICAL ERROR in control loop: {e}")
                    self.motor_funcs['stop']() # Attempt to stop motors on error
                finally:
                    self.automation_active.clear() # Clear the event, so it waits for next activation
                    self.automation_state = "IDLE" # Reset state for next mission
                    print("[AutomationController Thread] Automation loop reset to IDLE.")
            time.sleep(0.1) # Sleep briefly when automation is IDLE