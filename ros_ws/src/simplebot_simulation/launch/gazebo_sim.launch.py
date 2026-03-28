import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node

def generate_launch_description():
    # 1. Package Paths
    pkg_simulation = get_package_share_directory('simplebot_simulation')
    pkg_description = get_package_share_directory('simplebot_description')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')

    # 2. Files
    xacro_file = os.path.join(pkg_description, 'urdf', 'robots', 'simplebot_description.urdf.xacro')
    rviz_config = os.path.join(pkg_description, 'rviz', 'urdf_config.rviz')
    gz_bridge_config = os.path.join(pkg_simulation, 'config', 'ros_gz_bridge.yaml')

    # 3. Launch Configurations
    use_sim_time = LaunchConfiguration('use_sim_time')
    use_rviz = LaunchConfiguration('rviz')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true', description='Use simulation (Gazebo) clock if true'),
        DeclareLaunchArgument('rviz', default_value='true', description='Launch RViz2 if true'),

        # 4. Environment Variables
        # This allows Gazebo to find models and resources
        AppendEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            os.path.join(pkg_description, '..')
        ),

        # 5. Gazebo Sim
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={'gz_args': '-r -v 4 empty.sdf'}.items(),
        ),

        # 6. Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': Command(['xacro ', xacro_file]),
                'use_sim_time': use_sim_time
            }]
        ),

        # 7. Spawn Robot
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=['-topic', 'robot_description', '-name', 'simplebot2', '-z', '0.1'],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),

        # 8. Ros Gz Bridge
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'config_file': gz_bridge_config}],
            output='screen'
        ),

        # 9. Custom Mecanum Joint State Publisher
        Node(
            package='simplebot_description',
            executable='mecanum_joint_state_publisher',
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),

        # 10. RViz
        Node(
            package='rviz2',
            executable='rviz2',
            arguments=['-d', rviz_config],
            condition=IfCondition(use_rviz),
            parameters=[{'use_sim_time': use_sim_time}]
        ),
    ])