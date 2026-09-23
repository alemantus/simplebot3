import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, RegisterEventHandler, TimerAction
from launch.event_handlers import OnProcessStart
from launch.substitutions import LaunchConfiguration, Command, FindExecutable, PathJoinSubstitution
from launch.conditions import IfCondition
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from launch_ros.parameter_descriptions import ParameterValue
from ament_index_python.packages import get_package_share_directory
from moveit_configs_utils import MoveItConfigsBuilder

def generate_launch_description():
    use_sim_time = LaunchConfiguration("use_sim_time", default="false")
    use_rviz    = LaunchConfiguration("use_rviz",     default="true")

    # ── URDF / robot_description ───────────────────────────────────────────────
    # Use the combined xacro that includes BOTH the arm geometry AND the
    # ros2_control hardware block (with RoArmHardware plugin + serial_port param).
    urdf_xacro = PathJoinSubstitution([
        FindPackageShare("simplebot_description"),
        "urdf", "control_m2", "roarm_m2.urdf.xacro",
    ])

    robot_description_content = ParameterValue(
        Command([
            FindExecutable(name="xacro"), " ", urdf_xacro,
            " use_gazebo:=false",
        ]),
        value_type=str,
    )
    robot_description = {"robot_description": robot_description_content}

    # ── robot_state_publisher ──────────────────────────────────────────────────
    robot_state_publisher_node = Node(
        package="robot_state_publisher",
        executable="robot_state_publisher",
        output="screen",
        parameters=[robot_description, {"use_sim_time": use_sim_time}],
    )

    # ── ros2_control_node (controller manager + hardware plugin) ───────────────
    # This is the node that actually loads RoArmHardware and opens /dev/ttyUSB0.
    ros2_controllers_yaml = PathJoinSubstitution([
        FindPackageShare("simplebot_description"),
        "config", "ros2_controllers.yaml",
    ])

    ros2_control_node = Node(
        package="controller_manager",
        executable="ros2_control_node",
        output="screen",
        parameters=[robot_description, ros2_controllers_yaml],
    )

    # ── Controller spawners (delayed so controller_manager is ready) ───────────
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    hand_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["hand_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    gripper_controller_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["gripper_controller", "--controller-manager", "/controller_manager"],
        output="screen",
    )

    # Spawn controllers only after ros2_control_node has started
    delay_controllers = RegisterEventHandler(
        event_handler=OnProcessStart(
            target_action=ros2_control_node,
            on_start=[
                TimerAction(period=2.0, actions=[joint_state_broadcaster_spawner]),
                TimerAction(period=3.0, actions=[hand_controller_spawner]),
                TimerAction(period=3.5, actions=[gripper_controller_spawner]),
            ],
        )
    )

    # ── MoveIt config (for move_group + RViz) ─────────────────────────────────
    moveit_config = (
        MoveItConfigsBuilder("simplebot2", package_name="simplebot_description")
        .robot_description(
            file_path="urdf/control_m2/roarm_m2.urdf.xacro",
            mappings={"use_gazebo": "false"},
        )
        .robot_description_semantic(file_path="config/simplebot2.srdf")
        .robot_description_kinematics(file_path="config/kinematics.yaml")
        .trajectory_execution(file_path="config/moveit_controllers.yaml")
        .joint_limits(file_path="config/joint_limits.yaml")
        .sensors_3d(file_path="config/sensors_3d.yaml")
        .pilz_cartesian_limits(file_path="config/pilz_cartesian_limits.yaml")
        .to_moveit_configs()
    )

    # ── move_group ─────────────────────────────────────────────────────────────
    move_group_node = Node(
        package="moveit_ros_move_group",
        executable="move_group",
        output="screen",
        parameters=[
            moveit_config.to_dict(),
            {"use_sim_time": use_sim_time},
        ],
    )

    # ── joystick ──────────────────────────────────────────────────────────────────

    joystick_node = Node(
        package="joy",
        executable="joy_node",
        name="joy_node",
        output="screen",
        parameters=[{"use_sim_time": use_sim_time}],
    )

    # ── RViz ──────────────────────────────────────────────────────────────────
    rviz_config_file = os.path.join(
        get_package_share_directory("simplebot_gripper_moveit_config"),
        "config",
        "moveit.rviz",
    )
    rviz_node = Node(
        package="rviz2",
        executable="rviz2",
        name="rviz2_moveit",
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
        condition=IfCondition(use_rviz),
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            "use_sim_time",
            default_value="false",
            description="Use simulation clock (false = real hardware)",
        ),
        DeclareLaunchArgument(
            "use_rviz",
            default_value="true",
            description="Launch RViz with MoveIt plugin",
        ),
        robot_state_publisher_node,
        ros2_control_node,
        delay_controllers,
        move_group_node,
        rviz_node,
        joystick_node,
    ])
