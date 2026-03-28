from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        # Start static transform publisher
        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments=['0.013', '0', '0.098', '0', '0', '0', 'base_link', 'laser'],
            output='screen'
        ),
        # Node(
        # package='tf2_ros',
        # executable='static_transform_publisher',
        # name='tof_static_tf',
        # arguments=['0.10809', '0', '0.05045', '0', '2.356194', '0', 'base_link', 'tof']
        # ),
    ])