class GripperTools:
    def __init__(self, ros):
        self.ros = ros

    def open(self):
        return self.ros.send_action(
            "/gripper_controller/gripper_cmd",
            "control_msgs/action/GripperCommand",
            {
                "command": {
                    "position": 0.0,
                    "max_effort": 10.0
                }
            }
        )

    def close(self):
        return self.ros.send_action(
            "/gripper_controller/gripper_cmd",
            "control_msgs/action/GripperCommand",
            {
                "command": {
                    "position": -1.545,
                    "max_effort": 10.0
                }
            }
        )
