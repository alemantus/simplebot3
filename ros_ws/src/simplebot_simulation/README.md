# simplebot_simulation

This package contains the simulation environment for the `simplebot` robot in Gazebo Sim (Ignition).

## Overview

- `config/`: Contains the bridge configurations for `ros_gz_bridge`.
- `launch/`: Contains launch files to start the simulation, bridge, and related nodes.
- `rviz/`: Pre-configured RViz settings for visualization.
- `worlds/`: Gazebo world files.

## Launch Files

- `gazebo_sim.launch.py`: A basic launch file starting Gazebo with the robot and bridge.
- `simplebot_rosmaster.gazebo.launch.py`: A comprehensive launch file that includes SLAM, Navigation, and Joy-to-Pose mapping.

## Dependencies

This package depends on:
- `ros_gz_sim`
- `ros_gz_bridge`
- `simplebot_description`
- `simplebot2` (for SLAM configurations)
- `misc` (for joystick utilities)
