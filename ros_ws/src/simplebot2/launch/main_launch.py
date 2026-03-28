#!/home/alexander/venv/bin/python

from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, LogInfo
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_xml.launch_description_sources import XMLLaunchDescriptionSource
import os


def generate_launch_description():
    # Declare arguments for conditional configurations
    use_slam = DeclareLaunchArgument('use_slam', default_value='false', description='Launch SLAM nodes')
    use_nav = DeclareLaunchArgument('use_nav', default_value='false', description='Launch Navigation2 stack')
    use_nav2_wo_amcl = DeclareLaunchArgument('use_nav2_wo_amcl', default_value='true', description='Launch Navigation2 stack without amcl')
    use_camera = DeclareLaunchArgument('use_camera', default_value='false', description='Launch camera node')
    map_file = DeclareLaunchArgument(
        'map',
        default_value=os.path.join(
            get_package_share_directory('nav2_bringup'),
            'maps',
            'apartment_map/apartment.yaml'  # Replace with your map file name
        ),
        description='Full path to the map file to load'
    )
    log_level = DeclareLaunchArgument(
        'log_level',
        default_value='info',
        description='Logging level (debug, info, warn, error, fatal)'
    )

    # Paths to launch files
    cmd_vel_mux_path = os.path.join(get_package_share_directory('cmd_vel_mux'), 'launch', 'cmd_vel_mux-launch.py')
    foxglove_bridge_launch_path = os.path.join(get_package_share_directory('rosbridge_server'), 'launch', 'rosbridge_websocket_launch.xml')
    lidar_launch_path = os.path.join(get_package_share_directory('sllidar_ros2'), 'launch', 'lidar_launch.py')
    robot_control_launch_path = os.path.join(get_package_share_directory('motor_controller2'), 'launch', 'robot_control_launch.py')
    localization_launch_path = os.path.join(get_package_share_directory('simplebot2'), 'launch', 'localization_launch.py')
    joy_launch_path = os.path.join(get_package_share_directory('simplebot2'), 'launch', 'joy_launch.py')
    static_tf_path = os.path.join(get_package_share_directory('simplebot2'), 'launch', 'static_tf_launch.py')
    camera_launch_path = os.path.join(get_package_share_directory('camera_package'), 'launch', 'camera_launch.py')
    slam_launch_path = os.path.join(get_package_share_directory('simplebot2'), 'launch', 'online_async_launch.py')
    nav2_bringup_launch_path = os.path.join(get_package_share_directory('nav2_bringup'), 'launch', 'bringup_launch.py')
    nav2_bringup_wo_amcl_launch_path = os.path.join(get_package_share_directory('nav2_bringup'), 'launch', 'bringup_wo_amcl_launch.py')
    i2c_launch_path = os.path.join(get_package_share_directory('sensor_package'), 'launch', 'i2c_launch.py')
    joy2pose_launch_path = os.path.join(get_package_share_directory('misc'), 'launch', 'joy2pose_launch.py')

    return LaunchDescription([
        # Declare arguments
        use_slam,
        use_nav,
        use_camera,
        map_file,
        use_nav2_wo_amcl,
        log_level,

        # Always included components
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(robot_control_launch_path),
            launch_arguments={'log_level': LaunchConfiguration('log_level')}.items()
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(localization_launch_path),
            launch_arguments={'log_level': LaunchConfiguration('log_level')}.items()
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(static_tf_path),
            launch_arguments={'log_level': LaunchConfiguration('log_level')}.items()
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(lidar_launch_path),
            launch_arguments={'log_level': LaunchConfiguration('log_level')}.items()
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(joy_launch_path),
            launch_arguments={'log_level': LaunchConfiguration('log_level')}.items()
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(cmd_vel_mux_path),
            launch_arguments={'log_level': LaunchConfiguration('log_level')}.items()
        ),
        # IncludeLaunchDescription(
        #     XMLLaunchDescriptionSource(foxglove_bridge_launch_path),
        #     launch_arguments={'log_level': LaunchConfiguration('log_level')}.items()
        # ),
        #IncludeLaunchDescription(PythonLaunchDescriptionSource(i2c_launch_path)),
        # three launch mode
        # 1) nav2 with map
        #   - launch with use_nav:=true use_nav2_wo_amcl:= false use_slam:=false
        #   - TODO: add map as argument

        # 2) nav2 without amcl (slam provide map)
        #   - launch with use_nav:=false use_nav2_wo_amcl:=true use_slam:=true

        # 3) mapping mode with just slam
        #   - launch with use_nav:=false use_nav2_wo_amcl:=false use_slam:=true

        # mode 1) nav2 with map
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_bringup_launch_path),
            condition=IfCondition(LaunchConfiguration('use_nav')),
            launch_arguments={
                'map': LaunchConfiguration('map'),
                'log_level': LaunchConfiguration('log_level')
            }.items()
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(joy2pose_launch_path),
            condition=IfCondition(LaunchConfiguration('use_nav')),
            launch_arguments={'log_level': LaunchConfiguration('log_level')}.items()
        ),

        # mode 2) nav2 without amcl
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(nav2_bringup_wo_amcl_launch_path),
            condition=IfCondition(LaunchConfiguration('use_nav2_wo_amcl')),
            launch_arguments={'log_level': LaunchConfiguration('log_level')}.items()
        ),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(joy2pose_launch_path),
            condition=IfCondition(LaunchConfiguration('use_nav2_wo_amcl')),
            launch_arguments={'log_level': LaunchConfiguration('log_level')}.items()
        ),

        # mode 3) conditionally include SLAM
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(slam_launch_path),
            condition=IfCondition(LaunchConfiguration('use_slam')),
            launch_arguments={'log_level': LaunchConfiguration('log_level')}.items()
        ),

        # Conditionally include Camera
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(camera_launch_path),
            condition=IfCondition(LaunchConfiguration('use_camera')),
            launch_arguments={'log_level': LaunchConfiguration('log_level')}.items()
        ),

        # Log info
        LogInfo(condition=IfCondition(LaunchConfiguration('use_slam')), msg="SLAM is enabled"),
        LogInfo(condition=IfCondition(LaunchConfiguration('use_nav')), msg="Navigation is enabled"),
        LogInfo(condition=IfCondition(LaunchConfiguration('use_camera')), msg="Camera is enabled"),
    ])
