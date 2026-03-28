#!/usr/bin/env python3

from better_launch import BetterLaunch, launch_this


@launch_this
def sensors(
    imu: bool = True,
    neopixel: bool = True,
    i2c: bool = True
):

    bl = BetterLaunch()

    if neopixel:
        bl.node(
            package="sensor_package",
            executable="neopixel_indicator.py",
            name="neopixel"
        )

    if imu:
        bl.node(
            package="sensor_package",
            executable="lsm6dsm.py",
            name="imu"
        )

    if i2c:
        bl.node(
            package="sensor_package",
            executable="i2c_devices.py",
            name="i2c_devices"
        )