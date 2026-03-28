import os
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, Command
from launch.conditions import IfCondition
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory

def generate_launch_description():

    pkg_share = get_package_share_directory('simplebot_description')
    
    # Path to the main modular Xacro file
    default_model_path = os.path.join(pkg_share, 'urdf', 'robots', 'simplebot_description.urdf.xacro')
    default_rviz_config = os.path.join(pkg_share, 'rviz', 'urdf_config.rviz')

    # Launch configuration variables
    use_sim_time = LaunchConfiguration('use_sim_time')
    model = LaunchConfiguration('model')
    rviz_config = LaunchConfiguration('rviz_config')

    return LaunchDescription([

        DeclareLaunchArgument(
            name='use_sim_time',
            default_value='true',
            description='Use simulation clock if true'
        ),

        DeclareLaunchArgument(
            name='model',
            default_value=default_model_path,
            description='Path to URDF/Xacro file'
        ),

        DeclareLaunchArgument(
            name='rviz',
            default_value='true',
            description='Launch RViz'
        ),

        DeclareLaunchArgument(
            name='rviz_config',
            default_value=default_rviz_config,
            description='Path to RViz config file'
        ),

        # 1. Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': Command(['xacro ', model]),
                'use_sim_time': use_sim_time
            }]
        ),

        # 2. Mecanum Joint State Publisher (Bridge)
        Node(
            package='simplebot_description',
            executable='mecanum_joint_state_publisher',
            name='mecanum_joint_state_publisher',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}]
        ),

        # 3. RViz2
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            output='screen',
            arguments=['-d', rviz_config],
            condition=IfCondition(LaunchConfiguration('rviz')),
            parameters=[{'use_sim_time': use_sim_time}]
        ),
    ])