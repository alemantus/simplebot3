#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from yolo_msgs.msg import DetectionArray
import sys
import json
import time

class ObjectLocator(Node):
    def __init__(self, target_class):
        super().__init__('object_locator_tool')
        self.target_class = target_class
        self.found_msg = None
        
        self.sub = self.create_subscription(
            DetectionArray,
            '/yolo/detections_3d',
            self.callback,
            qos_profile_sensor_data)

    def callback(self, msg):
        for det in msg.detections:
            if det.class_name.lower() == self.target_class.lower():
                self.found_msg = {
                    "class_name": det.class_name,
                    "position": {
                        "x": round(det.bbox3d.center.position.x, 4),
                        "y": round(det.bbox3d.center.position.y, 4),
                        "z": round(det.bbox3d.center.position.z, 4)
                    },
                    "frame_id": det.bbox3d.frame_id,
                    "score": round(det.score, 2)
                }
                break

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Usage: locate_object.py <class_name>"}))
        return

    target = sys.argv[1]
    rclpy.init()
    node = ObjectLocator(target)
    
    # We use a short timeout as we expect the node to be already running and publishing
    start_time = time.time()
    timeout = 3.0
    
    try:
        while rclpy.ok() and time.time() - start_time < timeout:
            rclpy.spin_once(node, timeout_sec=0.1)
            if node.found_msg:
                print(json.dumps(node.found_msg, indent=2))
                return
        
        print(json.dumps({"success": False, "error": f"Object '{target}' not detected. Ensure segmentation_pcl_node is running and the object is in view."}, indent=2))
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
