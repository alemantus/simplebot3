import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time", default="true")

    # Build MoveIt config from simplebot_description package.
    # The URDF is the full robot (arm + base) with use_gazebo:=true so ros2_control
    # uses gz_ros2_control/GazeboSimSystem — matching the already-running Gazebo sim.
    moveit_config = (
        MoveItConfigsBuilder("simplebot2", package_name="simplebot_description")
        .robot_description(
            file_path="urdf/robots/simplebot_description.urdf.xacro",
            mappings={"use_gazebo": "true"},
        )
        .robot_description_semantic(file_path="config/simplebot2.srdf")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .joint_limits(file_path="config/joint_limits.yaml")
        .sensors_3d(file_path="config/sensors_3d.yaml")
        .pilz_cartesian_limits(file_path="config/pilz_cartesian_limits.yaml")
        .to_moveit_configs()
    )

    # move_group node — connects to controllers already running inside Gazebo.
    # Does NOT start its own ros2_control_node; Gazebo owns the controller_manager.
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": use_sim_time},
        ],
    )

    # RViz with MoveIt MotionPlanning plugin
    rviz_config_file = os.path.join(
        get_package_share_directory("simplebot_gripper_moveit_config"),
        "config",
        "moveit.rviz",
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2",
        output="log",
        arguments=["-d", rviz_config_file],
        parameters=[
            moveit_config.robot_description,
            moveit_config.robot_description_semantic,
            moveit_config.robot_description_kinematics,
            moveit_config.planning_pipelines,
            moveit_config.joint_limits,
            {"use_sim_time": use_sim_time},
        ],
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="true",
            description="Use Gazebo simulation clock",
        ),
        move_group_node,
        rviz_node,
    ])
