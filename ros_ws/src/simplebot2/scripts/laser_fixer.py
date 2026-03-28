#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan

class LaserFixer(Node):
    def __init__(self):
        super().__init__('laser_fixer')
        # Subscribe to the "broken" scan from Gazebo
        self.subscription = self.create_subscription(
            LaserScan,
            '/scan',
            self.listener_callback,
            10)
        # Publish the "fixed" scan for SLAM/Nav2
        self.publisher = self.create_publisher(LaserScan, '/scan_fixed', 10)

    def listener_callback(self, msg):
        # 1. Reverse the arrays to fix the "opposite rotation"
        msg.ranges = msg.ranges[::-1]
        if len(msg.intensities) > 0:
            msg.intensities = msg.intensities[::-1]
        
        # 2. Ensure the frame matches your URDF
        msg.header.frame_id = 'lidar_link'
        
        self.publisher.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = LaserFixer()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()