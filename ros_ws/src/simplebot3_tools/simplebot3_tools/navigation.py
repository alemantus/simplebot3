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
        if distance < 0:
            return self.backup(abs(distance), speed)

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

    def backup(self, distance, speed=0.15):
        """
        Drive the robot backward.
        :param distance: Distance in meters (positive value).
        :param speed: Speed in m/s.
        """
        return self.ros.send_action(
            "/backup",
            "nav2_msgs/action/BackUp",
            {
                "target": {
                    "x": float(abs(distance)),
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

    def navigate_to(self, x, y, yaw_degrees=0.0):
        """
        Navigate to an absolute pose on the map.
        :param x: Target X position in map frame.
        :param y: Target Y position in map frame.
        :param yaw_degrees: Target heading in map frame.
        """
        yaw_rad = math.radians(yaw_degrees)
        qz = math.sin(yaw_rad / 2.0)
        qw = math.cos(yaw_rad / 2.0)
        
        goal = {
            "pose": {
                "header": {
                    "frame_id": "map"
                },
                "pose": {
                    "position": {
                        "x": float(x),
                        "y": float(y),
                        "z": 0.0
                    },
                    "orientation": {
                        "x": 0.0,
                        "y": 0.0,
                        "z": float(qz),
                        "w": float(qw)
                    }
                }
            }
        }
        
        # Give this action up to 60 seconds to complete
        return self.ros.send_action(
            "/navigate_to_pose",
            "nav2_msgs/action/NavigateToPose",
            goal,
            timeout=60.0
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
