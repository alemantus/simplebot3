#!/usr/bin/env python3
import os
from launch import LaunchDescription
from launch.actions import (AppendEnvironmentVariable, DeclareLaunchArgument, 
                             IncludeLaunchDescription)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():
    # 1. Package Paths
    pkg_simulation = FindPackageShare('simplebot_simulation')
    pkg_description = FindPackageShare('simplebot_description')
    pkg_bot2 = FindPackageShare('simplebot2')
    pkg_misc = FindPackageShare('misc')
    pkg_nav2 = FindPackageShare('nav2_bringup')
    pkg_ros_gz_sim = FindPackageShare('ros_gz_sim')

    # 2. Launch Configurations
    use_sim_time = LaunchConfiguration('use_sim_time')
    robot_name = LaunchConfiguration('robot_name')
    world_file = LaunchConfiguration('world_file')
    headless = LaunchConfiguration('headless')
    log_level = LaunchConfiguration('log_level')
    
    pose = {k: LaunchConfiguration(k) for k in ['x', 'y', 'z', 'roll', 'pitch', 'yaw']}

    # 3. Paths to Files
    world_path = PathJoinSubstitution([pkg_simulation, 'worlds', world_file])
    gz_bridge_config = PathJoinSubstitution([pkg_simulation, 'config', 'ros_gz_bridge.yaml'])
    default_rviz_path = PathJoinSubstitution([pkg_simulation, 'rviz', 'yahboom_rosmaster_gazebo_sim.rviz'])

    # 4. Included Launch Actions
    # Robot State Publisher
    robot_state_publisher = IncludeLaunchDescription(
        PythonLaunchDescriptionSource([PathJoinSubstitution([pkg_description, 'launch', 'robot_state_publisher.launch.py'])]),
        launch_arguments={
            'enable_odom_tf': LaunchConfiguration('enable_odom_tf'),
            'jsp_gui': LaunchConfiguration('jsp_gui'),
            'rviz_config_file': LaunchConfiguration('rviz_config_file'),
            'use_rviz': LaunchConfiguration('use_rviz'),
            'use_gazebo': LaunchConfiguration('use_gazebo'),
            'use_sim_time': use_sim_time
        }.items(),
        condition=IfCondition(LaunchConfiguration('use_robot_state_pub'))
    )

    # SLAM Toolbox
    nav2_slam = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([pkg_bot2, 'launch', 'online_async_launch.py'])),
        condition=IfCondition(LaunchConfiguration('use_nav2_slam')),
        launch_arguments={
            'use_sim_time': use_sim_time, 
            'log_level': log_level, 
            'autostart': 'true', 
            'use_lifecycle_manager': 'false'
        }.items()
    )

    # Nav2 Bringup
    nav2_bringup = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(PathJoinSubstitution([pkg_nav2, 'launch', 'navigation_launch.py'])),
        condition=IfCondition(LaunchConfiguration('use_nav2')),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'autostart': 'true',
            'params_file': PathJoinSubstitution([pkg_nav2, 'params', 'nav2_params.yaml']),
            'use_lifecycle_manager': 'true',
            'log_level': log_level
        }.items()
    )

    # 5. Build Launch Description
    return LaunchDescription([
        # All DeclareLaunchArguments
        DeclareLaunchArgument('enable_odom_tf', default_value='true'),
        DeclareLaunchArgument('headless', default_value='False'),
        DeclareLaunchArgument('robot_name', default_value='simplebot'),
        DeclareLaunchArgument('rviz_config_file', default_value=default_rviz_path),
        DeclareLaunchArgument('load_controllers', default_value='true'),
        DeclareLaunchArgument('use_robot_state_pub', default_value='true'),
        DeclareLaunchArgument('jsp_gui', default_value='false'),
        DeclareLaunchArgument('use_rviz', default_value='true'),
        DeclareLaunchArgument('use_gazebo', default_value='true'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('world_file', default_value='empty.world'),
        DeclareLaunchArgument('use_nav2', default_value='true'),
        DeclareLaunchArgument('use_nav2_slam', default_value='true'),
        DeclareLaunchArgument('log_level', default_value='info'),
        *[DeclareLaunchArgument(k, default_value='2.5' if k in ['x', 'y'] else ('0.05' if k == 'z' else '0.0')) for k in pose.keys()],

        # Environment Variables
        # Add the directory containing the packages to Gazebo resource path so it can find meshes/models
        AppendEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            PathJoinSubstitution([pkg_description, '..'])
        ),

        # Launch Items
        robot_state_publisher,
        nav2_slam,
        nav2_bringup,
        
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([pkg_misc, 'launch', 'joy2pose_launch.py'])),
            condition=IfCondition(LaunchConfiguration('use_nav2')),
            launch_arguments={'log_level': log_level}.items()
        ),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([PathJoinSubstitution([pkg_description, 'launch', 'load_ros2_controllers.launch.py'])]),
            launch_arguments={'use_sim_time': use_sim_time}.items(),
            condition=IfCondition(LaunchConfiguration('load_controllers'))
        ),

        # Gazebo Actions
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py'])),
            launch_arguments=[('gz_args', [PythonExpression(["' -r -s ' + '", world_path, "'"])])]),
        
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(PathJoinSubstitution([pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py'])),
            launch_arguments={'gz_args': ['-g ']}.items(),
            condition=IfCondition(PythonExpression(['not ', headless]))),

        # Bridge Nodes
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{
                'config_file': gz_bridge_config,
                'use_sim_time': use_sim_time
            }],
            output='screen'
        ),
        
        Node(
            package='ros_gz_image',
            executable='image_bridge',
            arguments=['/cam_1/image'],
            remappings=[('/cam_1/image', '/cam_1/color/image_raw')],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),

        # Robot Spawner
        Node(
            package='ros_gz_sim',
            executable='create',
            output='screen',
            arguments=[
                '-topic', '/robot_description',
                '-name', robot_name,
                '-allow_renaming', 'true',
                '-x', pose['x'], '-y', pose['y'], '-z', pose['z'],
                '-R', pose['roll'], '-P', pose['pitch'], '-Y', pose['yaw']
            ]
        ),
    ])