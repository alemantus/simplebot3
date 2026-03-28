#!/usr/bin/python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import time

class CmdVelPublisher(Node):

    def __init__(self):
        super().__init__('cmd_vel_publisher')
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.timer_ = self.create_timer(1.0, self.publish_cmd_vel)

    def publish_cmd_vel(self):
        twist_msg = Twist()
        twist_msg.linear.x = 3.0  # Adjust the linear velocity as needed
        twist_msg.angular.z = 0.0  # Adjust the angular velocity as needed
        self.publisher_.publish(twist_msg)
        self.get_logger().info('Publishing cmd_vel: linear=%.2f, angular=%.2f' % (twist_msg.linear.x, twist_msg.angular.z))

def main(args=None):
    rclpy.init(args=args)
    cmd_vel_publisher = CmdVelPublisher()

    start_time = time.time()
    while rclpy.ok():
        rclpy.spin_once(cmd_vel_publisher)
        if time.time() - start_time > 2.0:
            break

    cmd_vel_publisher.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()