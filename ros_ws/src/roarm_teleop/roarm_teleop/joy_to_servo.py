#!/usr/bin/env python3
"""
Bridges a PS4 controller's /joy messages into MoveIt Servo's
/servo_node/delta_twist_cmds (Cartesian jogging) topic.

Default PS4 mapping via ds4drv / joy_node (VERIFY against `ros2 topic echo
/joy` while pressing each button once -- indices vary by driver):
  axes[0]  Left stick  X   (left = +1.0)
  axes[1]  Left stick  Y   (up   = +1.0)
  axes[3]  Right stick X
  axes[4]  Right stick Y
  axes[2]  L2 trigger      (released = +1.0, pressed = -1.0)
  axes[5]  R2 trigger      (released = +1.0, pressed = -1.0)
  buttons[4]  L1  (used here as the deadman / enable button)
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import TwistStamped
from moveit_msgs.srv import ServoCommandType


class JoyToServo(Node):

    def __init__(self):
        super().__init__('joy_to_servo')

        self.declare_parameter('deadman_button', 4)       # L1
        self.declare_parameter('linear_x_axis', 1)          # left stick Y -> fwd/back
        self.declare_parameter('linear_y_axis', 0)          # left stick X -> left/right
        self.declare_parameter('linear_z_up_axis', 5)       # R2 -> up
        self.declare_parameter('linear_z_down_axis', 2)     # L2 -> down
        self.declare_parameter('angular_x_axis', 4)         # right stick Y -> pitch
        self.declare_parameter('angular_y_axis', 3)         # right stick X -> roll
        self.declare_parameter('frame_id', 'base_link')
        self.declare_parameter('publish_rate_hz', 50.0)
        self.declare_parameter('deadzone', 0.05)

        self._p = lambda name: self.get_parameter(name).value

        self.latest_joy = None
        self.create_subscription(Joy, '/joy', self._joy_cb, 10)
        self.twist_pub = self.create_publisher(
            TwistStamped, '/servo_node/delta_twist_cmds', 10)

        period = 1.0 / self._p('publish_rate_hz')
        self.create_timer(period, self._timer_cb)

        self._set_command_type_on_startup()

        self.get_logger().info('joy_to_servo started, waiting for /joy...')

    def _set_command_type_on_startup(self):
        """Servo starts with no command type set and silently ignores every
        message until told what to expect. TWIST = 1 (see moveit_msgs/srv/
        ServoCommandType: 0=JointJog, 1=Twist, 2=Pose)."""
        client = self.create_client(
            ServoCommandType, '/servo_node/switch_command_type')
        if not client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error(
                'switch_command_type service not available -- '
                'is servo_node running?')
            return
        request = ServoCommandType.Request()
        request.command_type = 1  # Twist
        future = client.call_async(request)
        future.add_done_callback(self._on_command_type_set)

    def _on_command_type_set(self, future):
        try:
            result = future.result()
            if result.success:
                self.get_logger().info('Servo command type set to TWIST.')
            else:
                self.get_logger().warn(
                    'Servo rejected the TWIST command type request.')
        except Exception as exc:
            self.get_logger().error(f'switch_command_type call failed: {exc}')

    def _joy_cb(self, msg: Joy):
        self.latest_joy = msg

    def _deadzone(self, val: float) -> float:
        dz = self._p('deadzone')
        return 0.0 if abs(val) < dz else val

    def _axis(self, msg: Joy, index: int) -> float:
        if index is None or index < 0 or index >= len(msg.axes):
            return 0.0
        return msg.axes[index]

    def _timer_cb(self):
        twist = TwistStamped()
        twist.header.stamp = self.get_clock().now().to_msg()
        twist.header.frame_id = self._p('frame_id')

        msg = self.latest_joy
        deadman = self._p('deadman_button')

        held = (
            msg is not None
            and deadman is not None
            and 0 <= deadman < len(msg.buttons)
            and msg.buttons[deadman] == 1
        )

        if held:
            twist.twist.linear.x = self._deadzone(
                self._axis(msg, self._p('linear_x_axis')))
            twist.twist.linear.y = self._deadzone(
                self._axis(msg, self._p('linear_y_axis')))

            # Triggers: rest = +1.0, fully pressed = -1.0. Convert each to [0, 1]
            # and take the difference so up/down share one axis.
            z_up = (1.0 - self._axis(msg, self._p('linear_z_up_axis'))) / 2.0
            z_down = (1.0 - self._axis(msg, self._p('linear_z_down_axis'))) / 2.0
            twist.twist.linear.z = z_up - z_down

            twist.twist.angular.x = self._deadzone(
                self._axis(msg, self._p('angular_x_axis')))
            twist.twist.angular.y = self._deadzone(
                self._axis(msg, self._p('angular_y_axis')))
            twist.twist.angular.z = 0.0
        # else: leave twist as all-zero -- this actively tells Servo to stop,
        # rather than just not publishing (which could leave stale motion).

        self.twist_pub.publish(twist)


def main(args=None):
    rclpy.init(args=args)
    node = JoyToServo()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()