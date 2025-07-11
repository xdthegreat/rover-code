
# kinematics.py
import serial
import math
import time # Used for dt calculation within the class

# --- Kinematics Configuration ---
WHEEL_DIAMETER_MM = 134 # Your wheel diameter in mm
TRACK_WIDTH_MM = 230    # Distance between your drive wheels in mm

wheel_circumference_m = math.pi * (WHEEL_DIAMETER_MM / 1000.0)  # Convert to meters
rpm_to_mps = wheel_circumference_m / 60.0 # Convert RPM to meters/second
track_width_m = TRACK_WIDTH_MM / 1000.0 # Convert to meters


class SkidSteerOdometry:
    def __init__(self, track_width_m, alpha=0.02):
        self.x = 0.0      # meters
        self.y = 0.0      # meters
        self.theta = 0.0  # radians
        self.track_width = track_width_m
        self.alpha = alpha # Fusion factor for IMU and odometry (1 = only odometry, 0 = only IMU)
        self.last_update_time = time.time() # To calculate dt

    def normalize_angle_deg(self, angle_deg):
        """Normalizes an angle to be within -180 to 180 degrees."""
        while angle_deg > 180:
            angle_deg -= 360
        while angle_deg <= -180:
            angle_deg += 360
        return angle_deg

    def update(self, rpm_l, rpm_r, imu_yaw_deg):
        """Updates the robot's pose based on left and right wheel RPMs.
           rpm_l: RPM of the left wheel.
           rpm_r: RPM of the right wheel.
        """
        current_time = time.time()
        dt = current_time - self.last_update_time
        self.last_update_time = current_time

        if dt == 0: # Avoid division by zero if time hasn't advanced
            return

        # Convert RPM to linear speed in m/s
        v_l = rpm_l * rpm_to_mps
        v_r = rpm_r * rpm_to_mps

        # Calculate linear and angular velocity of the robot
        v = (v_r + v_l) / 2.0         # Linear velocity (m/s)
        omega = (v_r - v_l) / self.track_width # Angular velocity (rad/s)

        # Update pose using differential drive kinematics
        # Simple Euler integration
        self.theta += omega * dt
        # theta_odom += omega * dt
        imu_theta_rad = math.radians(imu_yaw_deg)
        theta_fused = self.alpha * self.theta + (1 - self.alpha) * imu_theta_rad
        self.theta = theta_fused
        
        self.x += v * math.cos(self.theta) * dt
        self.y += v * math.sin(self.theta) * dt

    def get_pose(self):
        """Returns the current pose (x, y, theta) in meters and degrees."""
        return (self.x, self.y, self.normalize_angle_deg(math.degrees(self.theta)))