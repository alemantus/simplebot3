#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Pose, Twist, TransformStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import Float64MultiArray
import math
import tf2_ros

class OdometryPublisher(Node):
    def __init__(self):
        super().__init__('odometry_publisher')
        
        # Parameters
        self.declare_parameter('track_width', 0.222)
        self.declare_parameter('wheel_base', 0.26)
        self.declare_parameter('odom_frame', 'odom')
        self.declare_parameter('base_frame', 'base_link')

        self.track_width = self.get_parameter('track_width').value
        self.wheel_base = self.get_parameter('wheel_base').value
        self.odom_frame = self.get_parameter('odom_frame').value
        self.base_frame = self.get_parameter('base_frame').value

        # Publishers & Subscriptions
        self.odom_pub = self.create_publisher(Odometry, 'odom', 50)
        self.tf_broadcaster = tf2_ros.TransformBroadcaster(self)
        
        self.create_subscription(
            Float64MultiArray,
            'encoder_data',
            self.encoder_callback,
            10)

        # State
        self.x = 0.0
        self.y = 0.0
        self.theta = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.vomega = 0.0
        
        self.last_time = self.get_clock().now()
        
        # Timer for publishing at a fixed rate (optional, can also pub on callback)
        self.timer = self.create_timer(0.05, self.update_and_publish) # 20 Hz

    def encoder_callback(self, msg):
        if len(msg.data) != 4:
            return
            
        # [front_left, front_right, rear_left, rear_right] in m/s
        fl, fr, rl, rr = msg.data

        # Refresh parameters in case they changed during runtime (calibration)
        self.track_width = self.get_parameter('track_width').value
        self.wheel_base = self.get_parameter('wheel_base').value

        # Mecanum inverse kinematics for velocities
        # k = (Lx + Ly) where Lx = track_width/2 and Ly = wheel_base/2
        k = (self.track_width + self.wheel_base) / 2.0
        
        self.vx = (fl + fr + rl + rr) * 0.25
        self.vy = (-fl + fr + rl - rr) * 0.25
        # Angular velocity formula for mecanum
        self.vomega = (-fl + fr - rl + rr) / (2.0 * (self.track_width + self.wheel_base))

    def update_and_publish(self):
        current_time = self.get_clock().now()
        dt = (current_time - self.last_time).nanoseconds / 1e9
        
        if dt <= 0:
            return

        # Update position (Euler integration)
        delta_x = (self.vx * math.cos(self.theta) - self.vy * math.sin(self.theta)) * dt
        delta_y = (self.vx * math.sin(self.theta) + self.vy * math.cos(self.theta)) * dt
        delta_th = self.vomega * dt

        self.x += delta_x
        self.y += delta_y
        self.theta += delta_th

        # Create Quaternion from theta
        qx = 0.0
        qy = 0.0
        qz = math.sin(self.theta / 2.0)
        qw = math.cos(self.theta / 2.0)

        # Create and publish TF
        t = TransformStamped()
        t.header.stamp = current_time.to_msg()
        t.header.frame_id = self.odom_frame
        t.child_frame_id = self.base_frame
        t.transform.translation.x = self.x
        t.transform.translation.y = self.y
        t.transform.translation.z = 0.0
        t.transform.rotation.x = qx
        t.transform.rotation.y = qy
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw
        self.tf_broadcaster.sendTransform(t)

        # Create and publish Odometry message
        odom = Odometry()
        odom.header.stamp = current_time.to_msg()
        odom.header.frame_id = self.odom_frame
        odom.child_frame_id = self.base_frame

        odom.pose.pose.position.x = self.x
        odom.pose.pose.position.y = self.y
        odom.pose.pose.orientation.x = qx
        odom.pose.pose.orientation.y = qy
        odom.pose.pose.orientation.z = qz
        odom.pose.pose.orientation.w = qw

        odom.twist.twist.linear.x = self.vx
        odom.twist.twist.linear.y = self.vy
        odom.twist.twist.angular.z = self.vomega

        self.odom_pub.publish(odom)
        self.last_time = current_time


def main(args=None):
    rclpy.init(args=args)
    node = OdometryPublisher()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()

