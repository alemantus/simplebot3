#!/bin/python3
import time
import board
from rainbowio import colorwheel
from adafruit_seesaw import seesaw, neopixel

import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray, String

class NeopixelNode(Node):
    def __init__(self,i2c):
        super().__init__('neopixel_node')

        # NeoPixel configuration
        self.NEOPIXEL_PIN = 14  # Pin number
        self.NEOPIXEL_NUM = 16  # Number of LEDs (max 60)

        self.i2c = i2c # Uses board.SCL and board.SDA
        self.ss = seesaw.Seesaw(self.i2c)

        # Initialize NeoPixels
        self.pixels = neopixel.NeoPixel(self.ss, self.NEOPIXEL_PIN, self.NEOPIXEL_NUM, auto_write=False)
        self.pixels.brightness = 0.5  # Default brightness

        # Pre-generated patterns
        self.patterns = {
            "rainbow": self.rainbow_pattern,
            "blink": self.blink_pattern,
            "off": self.off_pattern
        }

        # ROS 2 Subscribers
        self.control_sub = self.create_subscription(
            Float64MultiArray, '/led_control', self.led_control_callback, 10
        )
        self.pattern_sub = self.create_subscription(
            Float64MultiArray, '/pattern_control', self.pattern_control_callback, 10
        )

    def led_control_callback(self, msg):
        """Handles LED control messages."""
        if len(msg.data) < 6:
            self.get_logger().error("Invalid message format. Expected at least 6 values.")
            return

        start_idx = int(msg.data[0])
        stop_idx = int(msg.data[1])
        brightness = float(msg.data[2])
        color = (int(msg.data[3]), int(msg.data[4]), int(msg.data[5]))

        # Validate indexes
        if start_idx < 0 or stop_idx >= self.NEOPIXEL_NUM or start_idx > stop_idx:
            self.get_logger().error("Invalid start or stop index.")
            return

        self.pixels.brightness = brightness

        for i in range(start_idx, stop_idx + 1):
            self.pixels[i] = color
        self.pixels.show()

    def pattern_control_callback(self, msg):
        """Handles pattern selection messages."""
        pattern_func = int(msg.data[0])

        match pattern_func:
            case 0:
                self.blink_pattern(int(msg.data[1]), int(msg.data[2]), float(msg.data[3])) 
            case _:
                return "nope"


        # if pattern_func is None:
        #     self.get_logger().error(f"Pattern '{pattern_name}' not found.")
        # else:
        #     pattern_func()

    def rainbow_pattern(self):
        """Displays a rainbow pattern on the LEDs."""
        for j in range(25):
            for i in range(self.NEOPIXEL_NUM):
                rc_index = (i * 25 // self.NEOPIXEL_NUM) + j
                self.pixels[i] = colorwheel(rc_index & 255)
            self.pixels.show()
            time.sleep(0.01)

    def blink_pattern(self, repeat=3, color=1, duration=0.5):

        match(color):
            case 1: # white
                colors = (255, 255, 255)
            case 2: # red
                colors = (255, 0, 0)
            case 3: # green
                colors = (0, 255, 0)
            case _: # white
                colors = (255, 255, 255)

        """Makes the LEDs blink on and off."""
        print(f"repeat: {repeat}")
        for _ in range(int(repeat)):
            for i in range(self.NEOPIXEL_NUM):
                self.pixels[i] = colors
            self.pixels.show()
            time.sleep(duration)

            for i in range(self.NEOPIXEL_NUM):
                self.pixels[i] = (0, 0, 0)
            self.pixels.show()
            time.sleep(duration)

    def off_pattern(self):
        """Turns off all LEDs."""
        for i in range(self.NEOPIXEL_NUM):
            self.pixels[i] = (0, 0, 0)
        self.pixels.show()


def main(args=None):
    rclpy.init(args=args)
    node = NeopixelNode()
    node.blink_pattern(repeat=2, color=3, duration=0.2)

    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.blink_pattern(repeat=2, color=2, duration=0.2)
        time.sleep(0.4)
    finally:
        rclpy.shutdown()

if __name__ == '__main__':
    main()
