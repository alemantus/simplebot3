from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch_ros.actions import Node
from launch.substitutions import LaunchConfiguration

def generate_launch_description():
    channel_type = LaunchConfiguration('channel_type', default='serial')
    serial_port = LaunchConfiguration('serial_port', default='/dev/sllidar')
    serial_baudrate = LaunchConfiguration('serial_baudrate', default='460800')
    frame_id = LaunchConfiguration('frame_id', default='laser')
    inverted = LaunchConfiguration('inverted', default='false')
    angle_compensate = LaunchConfiguration('angle_compensate', default='true')
    scan_mode = LaunchConfiguration('scan_mode', default='Standard')

    return LaunchDescription([
        DeclareLaunchArgument('channel_type', default_value=channel_type, description='Lidar channel type'),
        DeclareLaunchArgument('serial_port', default_value=serial_port, description='Lidar serial port'),
        DeclareLaunchArgument('serial_baudrate', default_value=serial_baudrate, description='Lidar baudrate'),
        DeclareLaunchArgument('frame_id', default_value=frame_id, description='Lidar frame id'),
        DeclareLaunchArgument('inverted', default_value=inverted, description='Invert scan data'),
        DeclareLaunchArgument('angle_compensate', default_value=angle_compensate, description='Enable angle compensation'),
        DeclareLaunchArgument('scan_mode', default_value=scan_mode, description='Lidar scan mode'),

        Node(
            package='sllidar_ros2',
            executable='sllidar_node',
            name='sllidar_node',
            parameters=[{
                'channel_type': channel_type,
                'serial_port': serial_port,
                'serial_baudrate': serial_baudrate,
                'frame_id': frame_id,
                'inverted': inverted,
                'angle_compensate': angle_compensate,
                'scan_mode': scan_mode,
                'sample_rate': 1
            }],
            output='screen'
        ),
        
        # Add laser filter node
        Node(
            package='laser_filters',
            executable='scan_to_scan_filter_chain',
            name='lidar_filter',
            parameters=[{
                'filter_chain': '/path/to/lidar_filter.yaml'
            }],
            remappings=[
                ('scan', '/scan'),                # input from lidar
                ('scan_filtered', '/scan_filtered') # output topic
            ],
            output='screen'
        ),
    ])
