import math
import time

class ObjectInteractionTools:
    def __init__(self, ros):
        self.ros = ros

    def find_object(self, class_name, timeout=5.0):
        """
        Find an object by class name in the YOLO 3D detections.
        Returns the detection dictionary or None.
        """
        result = self.ros.subscribe_once("/yolo/detections_3d", "yolo_msgs/msg/DetectionArray", timeout=timeout)
        if not result or "msg" not in result or not result["msg"].get("detections"):
            return None
        
        for detection in result["msg"]["detections"]:
            if detection["class_name"] == class_name:
                return detection
        return None

    def align_with_object(self, class_name):
        """
        Rotate the robot to face the object perfectly.
        """
        obj = self.find_object(class_name)
        if not obj:
            return {"success": False, "error": f"Object '{class_name}' not found"}
        
        pos = obj["bbox3d"]["center"]["position"]
        # In base_link, x is forward, y is left.
        angle_rad = math.atan2(pos["y"], pos["x"])
        angle_deg = math.degrees(angle_rad)
        
        if abs(angle_deg) < 2.0:
            return {"success": True, "message": "Already aligned within tolerance"}
            
        # Use spin action (relative rotation)
        return self.ros.send_action(
            "/spin",
            "nav2_msgs/action/Spin",
            {
                "target_yaw": float(angle_rad),
                "time_allowance": {"sec": 15}
            }
        )

    def approach_object(self, class_name, standoff_distance=0.3):
        """
        Complete sequence: find, align, and drive to a standoff distance.
        """
        # 1. Initial alignment
        align_res = self.align_with_object(class_name)
        if not align_res.get("success", True):
            return align_res

        # 2. Re-sense distance after alignment
        time.sleep(0.5)  # Wait for sensors to settle
        obj = self.find_object(class_name)
        if not obj:
             return {"success": False, "error": f"Object '{class_name}' lost after alignment"}
        
        current_x = obj["bbox3d"]["center"]["position"]["x"]
        move_dist = current_x - standoff_distance
        
        if abs(move_dist) < 0.05:
            return {"success": True, "message": f"Already at standoff ({current_x:.2f}m)"}
            
        # 3. Move to standoff
        if move_dist > 0:
            return self.ros.send_action(
                "/drive_on_heading",
                "nav2_msgs/action/DriveOnHeading",
                {
                    "target": {"x": float(move_dist), "y": 0.0, "z": 0.0},
                    "speed": 0.2,
                    "time_allowance": {"sec": 30}
                }
            )
        else:
            return self.ros.send_action(
                "/backup",
                "nav2_msgs/action/BackUp",
                {
                    "target": {"x": float(abs(move_dist)), "y": 0.0, "z": 0.0},
                    "speed": 0.15,
                    "time_allowance": {"sec": 30}
                }
            )

    def reach_object(self, class_name, offset_z=0.05, offset_x=0.0):
        """
        Move the arm to the object's 3D coordinates.
        :param offset_z: Height offset above object center.
        :param offset_x: Distance offset (positive = further into object).
        """
        obj = self.find_object(class_name)
        if not obj:
            return {"success": False, "error": f"Object '{class_name}' not found"}
        
        pos = obj["bbox3d"]["center"]["position"]
        
        # Target Cartesian coords in base_link
        target_x = pos["x"] + offset_x
        target_y = pos["y"]
        target_z = pos["z"] + offset_z
        
        # Call IK and Move (using existing pattern)
        # Note: Since this is in a separate tool, we'd ideally call ArmTools.move_to_xyz
        # But for simplicity in this script, we'll re-implement the IK logic or assume
        # the assistant uses this to get coords then calls move_arm_xyz.
        
        return {
            "success": True, 
            "target": {"x": target_x, "y": target_y, "z": target_z},
            "message": f"Coordinates for {class_name} calculated. Use move_arm_xyz with these values."
        }
