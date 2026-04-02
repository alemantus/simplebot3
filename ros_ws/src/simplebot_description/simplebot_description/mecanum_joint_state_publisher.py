#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState

class MecanumJointStatePublisher(Node):
    def __init__(self):
        super().__init__('mecanum_joint_state_publisher')
        
        # Declare parameters
        self.declare_parameter('joint_names', [
            "front_left_wheel_joint",
            "front_right_wheel_joint",
            "rear_left_wheel_joint",
            "rear_right_wheel_joint"
        ])
        self.declare_parameter('encoder_topic', '/encoder_data_gz')
        
        self.target_joint_names = self.get_parameter('joint_names').get_parameter_value().string_array_value
        encoder_topic = self.get_parameter('encoder_topic').get_parameter_value().string_value

        # Subscription to the bridged Gazebo topic or encoder source
        self.subscription = self.create_subscription(
            JointState,
            encoder_topic,
            self.joint_callback,
            10
        )

        # Publisher to the standard ROS topic
        self.publisher = self.create_publisher(JointState, '/joint_states', 10)
        
        self.get_logger().info(f"✓ Mecanum JointState Bridge Started. Subscribed to: {encoder_topic}")

    def joint_callback(self, msg):
        """
        Receives JointState (e.g. from Gazebo bridge) and ensures it is published 
        correctly for robot_state_publisher.
        """
        js = JointState()
        js.header.stamp = self.get_clock().now().to_msg()
        js.name = self.target_joint_names

        # Map input positions to output
        if len(msg.position) >= len(self.target_joint_names):
            js.position = list(msg.position[:len(self.target_joint_names)])
            
            # Optional: Pass velocities through as well
            if len(msg.velocity) >= len(self.target_joint_names):
                js.velocity = list(msg.velocity[:len(self.target_joint_names)])

            self.publisher.publish(js)

def main(args=None):
    rclpy.init(args=args)
    node = MecanumJointStatePublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == "__main__":
    main()