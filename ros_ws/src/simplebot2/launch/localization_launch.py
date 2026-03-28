from launch import LaunchDescription
from ament_index_python.packages import get_package_share_directory
from launch_ros.actions import Node
import os

def generate_launch_description():
    robot_localization_file_path = os.path.join(get_package_share_directory('simplebot2'), 'config', 'ekf2.yaml')
    
    return LaunchDescription([
        Node(
            package='robot_localization',
            executable='ekf_node',
            name='ekf_filter_node',
            output='screen',
            parameters=[robot_localization_file_path, {'use_sim_time': False}]
        )
    ])
