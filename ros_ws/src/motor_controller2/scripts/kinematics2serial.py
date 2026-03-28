#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.parameter import Parameter
from rcl_interfaces.msg import SetParametersResult
from geometry_msgs.msg import Twist
import threading
import serial
import time
from sensor_msgs.msg import Joy
import math
from std_msgs.msg import Float64MultiArray

class MechDriveNode(Node):
    def __init__(self):
        super().__init__('mech_drive_node')

        # Declare parameters
        self.declare_parameter('VEL_KP', 3.0)
        self.declare_parameter('VEL_KI', 0.0)
        self.declare_parameter('VEL_KD', 0.002)
        self.declare_parameter('serial_port', '/dev/motor_controller')
        self.declare_parameter('baud_rate', 115200)
        self.declare_parameter('wheel_radius', 0.035)
        self.declare_parameter('track_width', 0.222)
        self.declare_parameter('wheel_base', 0.26)

        # Cache values
        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.wheel_circumference = 2 * math.pi * self.wheel_radius
        self.track_width = self.get_parameter('track_width').value
        self.wheel_base = self.get_parameter('wheel_base').value
        
        # Add parameter change callback
        self.add_on_set_parameters_callback(self.parameter_callback)

        # Subscriptions
        self.create_subscription(Twist, '/cmd_vel', self.velocity_callback, 10)

        # Publishers
        self.encoder_pub = self.create_publisher(Float64MultiArray, '/encoder_data', 10)

        # Serial setup
        port = self.get_parameter('serial_port').value
        baud = self.get_parameter('baud_rate').value
        try:
            self.ser = serial.Serial(port, baudrate=baud, timeout=1.0)
            self.get_logger().info(f"Connected to serial port {port} at {baud}")
        except Exception as e:
            self.get_logger().error(f"Failed to open serial port {port}: {e}")
            raise e

        # Start the thread for reading serial responses
        self.running = True
        self.serial_thread = threading.Thread(target=self.read_serial)
        self.serial_thread.daemon = True
        self.serial_thread.start()

    def parameter_callback(self, params):
        for param in params:
            if param.name in ['VEL_KP', 'VEL_KI', 'VEL_KD']:
                self.get_logger().info(f"Parameter {param.name} updated to {param.value}")
                self.update_pid(param.name, param.value)
            elif param.name == 'wheel_radius':
                self.wheel_radius = param.value
                self.wheel_circumference = 2 * math.pi * self.wheel_radius
            elif param.name == 'track_width':
                self.track_width = param.value
            elif param.name == 'wheel_base':
                self.wheel_base = param.value

        return SetParametersResult(successful=True)

    def update_pid(self, name, value):
        params = f"{name}:{value}\n".encode() # Added \n for consistency
        try:
            self.ser.write(params)
            self.get_logger().info(f"Wrote PID parameter: {params.decode().strip()}")
        except Exception as e:
            self.get_logger().error(f"Error updating PID: {e}")

    def read_serial(self):
        while rclpy.ok() and self.running:
            if not self.ser.is_open:
                time.sleep(0.1)
                continue
            try:
                line = self.ser.readline().decode().strip()
                if line:
                    if "PID" in line:
                        self.get_logger().info(f"Serial response: {line}")
                    else:
                        try:
                            encoder_data = [float(val) for val in line.split(' ')]
                            if len(encoder_data) == 4:
                                self.publish_encoder_data(encoder_data)
                        except ValueError:
                            pass
            except Exception as e:
                self.get_logger().warning(f"Serial read error: {e}")

    def publish_encoder_data(self, encoder_data):
        # encoder_data is in rotations per second? 
        # Convert to m/s based on circumference
        encoder_data_mps = [val * self.wheel_circumference for val in encoder_data]
        msg = Float64MultiArray(data=encoder_data_mps)
        self.encoder_pub.publish(msg)

    def send_motor_commands(self, front_left, front_right, back_left, back_right):
        command = f"{front_left},{front_right},{back_left},{back_right}\n".encode()
        try:
            self.ser.write(command)
        except Exception as e:
            self.get_logger().error(f"Error writing motor command: {e}")

    def velocity_callback(self, msg):
        # Refresh parameters in case they changed during runtime (calibration)
        self.wheel_radius = self.get_parameter('wheel_radius').value
        self.track_width = self.get_parameter('track_width').value
        self.wheel_base = self.get_parameter('wheel_base').value
        
        speed_x = float(msg.linear.x)
        speed_y = float(msg.linear.y)
        rotation_z = float(msg.angular.z)
        fl, fr, bl, br = self.calculate_wheel_speeds(speed_x, speed_y, rotation_z)
        self.send_motor_commands(fl, fr, bl, br)

    def calculate_wheel_speeds(self, speed_x, speed_y, rotation_z):
        # Mecanum kinematics:
        # Lx = track_width / 2, Ly = wheel_base / 2
        # k = Lx + Ly
        k = (self.track_width + self.wheel_base) / 2.0
        inv_r = 1.0 / self.wheel_radius
        
        # Standard formulas for rotation per second (RPS)
        # Note: (2 * math.pi) converts rad/s to RPS
        fl = (speed_x - speed_y - k * rotation_z) * inv_r / (2 * math.pi)
        fr = (speed_x + speed_y + k * rotation_z) * inv_r / (2 * math.pi)
        bl = (speed_x + speed_y - k * rotation_z) * inv_r / (2 * math.pi)
        br = (speed_x - speed_y + k * rotation_z) * inv_r / (2 * math.pi)
        
        return round(fl, 3), round(fr, 3), round(bl, 3), round(br, 3)

    def stop_motors(self):
        self.send_motor_commands(0, 0, 0, 0)
        self.running = False


def main(args=None):
    rclpy.init(args=args)
    node = MechDriveNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.stop_motors()
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

