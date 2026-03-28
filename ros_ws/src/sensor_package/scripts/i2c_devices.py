#!/home/alexander/venv/bin/python
import time
import board
from rainbowio import colorwheel
from adafruit_seesaw import seesaw, neopixel
from rclpy.executors import MultiThreadedExecutor

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, String

from lsm6dsm import IMUNode
from neopixel_indicator import NeopixelNode




def main(args=None):
    rclpy.init(args=args)
    
    time.sleep(1)

    # Initialize IMU node
    i2c = board.I2C()  # or board.SCL and board.SDA if not using STEMMA I2C
    imu_node = IMUNode(i2c)

    time.sleep(1)
    # Initialize NeoPixel node
    neopixel_node = NeopixelNode(i2c)
    neopixel_node.blink_pattern(2, 3, 0.2)
    time.sleep(0.5)

    # Spin both nodes
    try:
        rclpy.spin(imu_node)
    except KeyboardInterrupt:
        pass

    time.sleep(0.5)
    try:
        rclpy.spin(neopixel_node)
    except KeyboardInterrupt:
        pass
    
    # Cleanup
    neopixel_node.blink_pattern(2, 2, 0.2)
    neopixel_node.off_pattern()
    imu_node.destroy_node()
    neopixel_node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()