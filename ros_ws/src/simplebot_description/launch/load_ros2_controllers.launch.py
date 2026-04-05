#!/usr/bin/env python3
from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Joint State Broadcaster: Publishes joint states to /joint_states
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
    )

    # 2. Mecanum Drive Controller: Handles cmd_vel and wheel transforms
    mecanum_drive_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["mecanum_drive_controller", "--controller-manager", "/controller_manager"],
    )

    # 3. Hand Controller: MoveIt manipulation arm
    hand_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["hand_controller", "--controller-manager", "/controller_manager"],
    )

    # 4. Gripper Controller: MoveIt gripper action
    gripper_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "--controller-manager", "/controller_manager"],
    )

    return LaunchDescription([
        joint_state_broadcaster_spawner,
        mecanum_drive_controller_spawner,
        hand_controller_spawner,
        gripper_controller_spawner,
    ])