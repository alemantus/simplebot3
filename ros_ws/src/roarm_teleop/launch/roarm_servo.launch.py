import os
import yaml
from launch import LaunchDescription
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder


def load_yaml(package_name, file_path):
    package_path = get_package_share_directory(package_name)
    absolute_path = os.path.join(package_path, file_path)
    with open(absolute_path, "r") as f:
        return yaml.safe_load(f)


def generate_launch_description():
    # Mirrors simplebot_bringup.launch.py's moveit_config exactly, so Servo
    # sees the same robot model / SRDF / kinematics as move_group does.
    moveit_config = (
        MoveItConfigsBuilder("simplebot2", package_name="simplebot_description")
        .robot_description(
            file_path="urdf/control_m2/roarm_m2.urdf.xacro",
            mappings={"use_gazebo": "false"},
        )
        .robot_description_semantic(file_path="config/simplebot2.srdf")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .joint_limits(file_path="config/joint_limits.yaml")
        .pilz_cartesian_limits(file_path="config/pilz_cartesian_limits.yaml")
        .to_moveit_configs()
    )

    servo_yaml = load_yaml("roarm_teleop", "config/roarm_servo_config.yaml")
    servo_params = {"moveit_servo": servo_yaml["moveit_servo"]}

    servo_node = Node(
        package="moveit_servo",
        executable="servo_node",
        name="servo_node",
        parameters=[
            servo_params,
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
        ],
        output="screen",
    )

    joy_to_servo_node = Node(
        package="roarm_teleop",
        executable="joy_to_servo",
        name="joy_to_servo",
        output="screen",
    )

    # joy_node is intentionally NOT launched here: simplebot_bringup.launch.py
    # already starts it. Run bringup first, then this launch file alongside it.
    return LaunchDescription([servo_node, joy_to_servo_node])