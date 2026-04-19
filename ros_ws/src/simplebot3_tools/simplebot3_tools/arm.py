class ArmTools:
    def __init__(self, ros):
        self.ros = ros

    def move_to_xyz(self, x, y, z):
        # 1. Solve IK
        ik_result = self.ros.call_service(
            "/compute_ik",
            "moveit_msgs/srv/GetPositionIK",
            {
                "ik_request": {
                    "group_name": "hand",
                    "pose_stamped": {
                        "header": {"frame_id": "base_link"},
                        "pose": {
                            "position": {"x": x, "y": y, "z": z},
                            "orientation": {"x": 0, "y": 0, "z": 0, "w": 1}
                        }
                    }
                }
            }
        )

        # Check if the result structure is what we expect
        if not ik_result or "error_code" not in ik_result.get("result", {}):
            return {"success": False, "error": "IK Service failed or returned invalid response", "raw": ik_result}

        if ik_result["result"]["error_code"]["val"] != 1:
            return {"success": False, "error": f"IK failed with error code {ik_result['result']['error_code']['val']}"}

        joints = ik_result["result"]["solution"]["joint_state"]

        # extract correct joints
        names = joints["name"]
        positions = joints["position"]

        joint_map = dict(zip(names, positions))

        try:
            target_positions = [
                joint_map["roarm_base_link_to_link1"],
                joint_map["link1_to_link2"],
                joint_map["link2_to_link3"],
                joint_map["link3_to_link4"],
                joint_map["link4_to_link5"],
            ]
        except KeyError as e:
            return {"success": False, "error": f"Missing joint in IK solution: {str(e)}"}

        # 2. Move arm
        return self.ros.send_action(
            "/hand_controller/follow_joint_trajectory",
            "control_msgs/action/FollowJointTrajectory",
            {
                "trajectory": {
                    "joint_names": [
                        "roarm_base_link_to_link1",
                        "link1_to_link2",
                        "link2_to_link3",
                        "link3_to_link4",
                        "link4_to_link5"
                    ],
                    "points": [{
                        "positions": target_positions,
                        "time_from_start": {"sec": 3}
                    }]
                }
            }
        )
