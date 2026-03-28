#!/bin/python3
import rclpy
from rclpy.node import Node
from tf2_ros import TransformListener, Buffer
from geometry_msgs.msg import PoseStamped
from sensor_msgs.msg import Joy

class RobotPoseNode(Node):
    def __init__(self):
        super().__init__('robot_pose_node')
        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)

        # Subscribe to the joy topic
        self.joy_subscriber = self.create_subscription(Joy, 'joy', self.joy_callback, 10)

        # Publisher for PoseStamped goal
        self.pose_publisher = self.create_publisher(PoseStamped, 'goal_pose', 10)

        self.saved_pose = None
        self.get_logger().info("RobotPoseNode initialized and ready.")

    def joy_callback(self, msg):
        if len(msg.buttons) >= 10:
            if msg.buttons[8]:  # Button 8 (index 7)
                self.save_pose()
            elif msg.buttons[7]:  # Button 9 (index 8)
                self.publish_saved_pose()

    def save_pose(self):
        try:
            now = rclpy.time.Time()
            transform = self.tf_buffer.lookup_transform(
                'map', 'base_link', now, timeout=rclpy.duration.Duration(seconds=1.0)
            )

            # Create a PoseStamped message
            pose = PoseStamped()
            pose.header.stamp = self.get_clock().now().to_msg()
            pose.header.frame_id = 'map'
            pose.pose.position.x = transform.transform.translation.x
            pose.pose.position.y = transform.transform.translation.y
            pose.pose.position.z = transform.transform.translation.z
            pose.pose.orientation = transform.transform.rotation

            self.saved_pose = pose
            self.get_logger().info("Pose saved successfully.")

        except Exception as e:
            self.get_logger().warn(f"Failed to save pose: {e}")

    def publish_saved_pose(self):
        if self.saved_pose:
            self.pose_publisher.publish(self.saved_pose)
            self.get_logger().info("Published saved pose as a goal.")
        else:
            self.get_logger().warn("No pose saved to publish.")

def main(args=None):
    rclpy.init(args=args)
    node = RobotPoseNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
