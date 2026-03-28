from launch import LaunchDescription
from launch_ros.actions import Node

def generate_launch_description():
    return LaunchDescription([
        Node(
            package='misc',  # Replace with the actual package name
            executable='joy2pose.py',  # Replace with the actual executable name
            name='joy2pose',  # Optional: Rename the node if needed
            output='screen',  # Prints the log to the terminal
            parameters=[{
                # Add parameters here if needed
                # 'param_name': param_value,
            }]
        )
    ])
