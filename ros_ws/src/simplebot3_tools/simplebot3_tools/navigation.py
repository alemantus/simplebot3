import math

class NavigationTools:
    def __init__(self, ros):
        self.ros = ros

    def drive_straight(self, distance, speed=0.2):
        """
        Drive the robot in a straight line (forward or backward).
        :param distance: Distance in meters (positive = forward, negative = backward).
        :param speed: Speed in m/s.
        """
        # Distinguish between forward and backward
        # Note: If /backup action is not available, we try /drive_on_heading with negative X
        # or use the appropriate behavior.
        action_name = "/drive_on_heading"
        action_type = "nav2_msgs/action/DriveOnHeading"
        
        return self.ros.send_action(
            action_name,
            action_type,
            {
                "target": {
                    "x": float(distance),
                    "y": 0.0,
                    "z": 0.0
                },
                "speed": float(speed),
                "time_allowance": {"sec": 30}
            }
        )

    def turn(self, angle_degrees, speed=0.5):
        """
        Rotate the robot in place.
        :param angle_degrees: Angle in degrees (positive = counter-clockwise).
        :param speed: Angular speed (if supported by action).
        """
        angle_radians = math.radians(angle_degrees)
        return self.ros.send_action(
            "/spin",
            "nav2_msgs/action/Spin",
            {
                "target_yaw": float(angle_radians),
                "time_allowance": {"sec": 30}
            }
        )

    def stop(self):
        """
        Stop the robot by cancelling active navigation goals.
        Note: This depends on the ros_interface supporting a way to cancel actions, 
        or we can try to send a zero-distance goal to override.
        """
        # For now, we'll implement this as a "cancel" if the interface supports it,
        # or a very short 'wait' or 'spin 0' to preempt.
        # However, the most effective way in some cases is to send a 0-velocity publish
        # but the guide forbids /cmd_vel directly. 
        # So we try to send a cancel op via the interface if possible.
        if hasattr(self.ros, 'cancel_all_actions'):
            return self.ros.cancel_all_actions()
            
        # Fallback: send a 0-radian spin to preempt active behaviors
        return self.turn(0.0)
