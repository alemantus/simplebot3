#!/usr/bin/python3

# SPDX-License-Identifier: MIT
import time
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Imu
from geometry_msgs.msg import Quaternion, Vector3
import numpy as np
import board
from adafruit_lsm6ds.lsm6dsox import LSM6DSOX
from adafruit_lsm6ds import Rate, AccelRange, GyroRange

class IMUNode(Node):    
    def __init__(self, i2c):
        super().__init__('imu_publisher')
        self.publisher_ = self.create_publisher(Imu, '/imu/data', 30)
        self.timer_ = self.create_timer(1/100, self.publish_imu_data)
        self.i2c = i2c # uses board.SCL and board.SDA
        # i2c = board.STEMMA_I2C()  # For using the built-in STEMMA QT connector on a microcontroller
        self.sensor = LSM6DSOX(self.i2c)

        self.sensor.accelerometer_range = AccelRange.RANGE_8G
        self.sensor.gyro_range = GyroRange.RANGE_2000_DPS

    def publish_imu_data(self):
        imu_msg = Imu()
        imu_msg.header.stamp = self.get_clock().now().to_msg()
        imu_msg.header.frame_id = 'imu_link'
        
        # Populate orientation (setting it to identity quaternion for simplicity)
        # imu_msg.orientation = Quaternion(x=0.0, y=0.0, z=0.0, w=1.0)
        
        # Populate orientation covariance (assuming identity matrix)
        imu_msg.orientation_covariance = [-1] * 9
        
        # Populate angular velocity
        imu_msg.angular_velocity = Vector3(
            x=self.sensor.gyro[0], 
            y=self.sensor.gyro[1], 
            z=self.sensor.gyro[2]
        )
        
        # Populate angular velocity covariance (assuming identity matrix)
        imu_msg.angular_velocity_covariance = [0.0] * 9
        
        # Populate linear acceleration
        imu_msg.linear_acceleration = Vector3(
            x=self.sensor.acceleration[0], 
            y=self.sensor.acceleration[1], 
            z=self.sensor.acceleration[2]
        )
        
        # Populate linear acceleration covariance (assuming identity matrix)
        # imu_msg.linear_acceleration_covariance = [0.0] * 9
        
        self.publisher_.publish(imu_msg)

def main(args=None):
    rclpy.init(args=args)
    imu_node = IMUNode()
    rclpy.spin(imu_node)
    imu_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
