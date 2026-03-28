import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument, AppendEnvironmentVariable
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import Command, LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    pkg_description = get_package_share_directory('simplebot_description')
    pkg_simulation = get_package_share_directory('simplebot_simulation')
    pkg_simplebot2 = get_package_share_directory('simplebot2')
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_nav2 = get_package_share_directory('nav2_bringup')
    pkg_slam_toolbox = get_package_share_directory('slam_toolbox')
    
    # Files
    xacro_file = os.path.join(pkg_description, 'urdf', 'robots', 'simplebot_description.urdf.xacro')
    gz_bridge_config = os.path.join(pkg_simulation, 'config', 'ros_gz_bridge.yaml')
    nav2_params = os.path.join(pkg_simplebot2, 'config', 'nav2_params.yaml')
    world_file = os.path.join(pkg_simulation, 'worlds', 'empty.world')
    rviz_config = os.path.join(pkg_simulation, 'rviz', 'yahboom_rosmaster_gazebo_sim.rviz')
    slam_params = os.path.join(pkg_simplebot2, 'config', 'mapper_params_online_async.yaml')
    twist_mux_config = os.path.join(pkg_simplebot2, 'config', 'twist_mux.yaml')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true', description='Use sim time'),
        DeclareLaunchArgument('cmd_vel_out',  default_value='/mecanum_drive_controller/reference', description='cmd vel output topic'),
        
        # Set Gazebo resource path for meshes
        AppendEnvironmentVariable(
            'GZ_SIM_RESOURCE_PATH',
            os.path.join(pkg_description, '..')
        ),

        # 1. Gazebo Sim
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
            ),
            launch_arguments={'gz_args': f'-r {world_file}'}.items(),
        ),

        # 2. Robot State Publisher
        Node(
            package='robot_state_publisher',
            executable='robot_state_publisher',
            parameters=[{
                'robot_description': Command(['xacro ', xacro_file, ' use_gazebo:=true']),
                'use_sim_time': use_sim_time
            }]
        ),

        # 3. Spawn Robot
        Node(
            package='ros_gz_sim',
            executable='create',
            arguments=['-topic', 'robot_description', '-name', 'simplebot2', '-z', '1.0'],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),

        # 4. ROS Gz Bridge
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            parameters=[{'config_file': gz_bridge_config, 'use_sim_time': use_sim_time}],
            output='screen'
        ),

        # 5. Image Bridge
        Node(
            package='ros_gz_image',
            executable='image_bridge',
            name='gz_image_bridge',
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'
        ),

        # 6. ROS2 Controllers (Standard controller_manager spawners)
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["joint_state_broadcaster", "--controller-manager", "/controller_manager"],
            parameters=[{'use_sim_time': use_sim_time}],
        ),
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["mecanum_drive_controller", "--controller-manager", "/controller_manager"],
            parameters=[{'use_sim_time': use_sim_time}],
        ),
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["hand_controller", "--controller-manager", "/controller_manager"],
            parameters=[{'use_sim_time': use_sim_time}],
        ),
        Node(
            package="controller_manager",
            executable="spawner",
            arguments=["gripper_controller", "--controller-manager", "/controller_manager"],
            parameters=[{'use_sim_time': use_sim_time}],
        ),


        # 7. Nav2 Online Async SLAM (Standard package) 
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_slam_toolbox, 'launch', 'online_async_launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time, 
                'slam_params_file': slam_params,
                'log_level': 'error',
                'enable_stamped_cmd_vel': 'true'
            }.items()
        ),

        # 8. Nav2 Bringup Navigation (Standard package)
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_nav2, 'launch', 'navigation_launch.py')
            ),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'params_file': nav2_params,
                'run_amcl': 'false',
                'use_lifecycle_manager': 'true',
                'log_level': 'error',
                'enable_stamped_cmd_vel': 'true'
            }.items()
        ),
        
        # 9. RViz
        # Node(
        #     package='rviz2',
        #     executable='rviz2',
        #     name='rviz2',
        #     output='screen',
        #     arguments=['-d', rviz_config],
        #     parameters=[{'use_sim_time': use_sim_time}]
        # ),

        # 10. Twist Mux
        Node(
            package='twist_mux',
            executable='twist_mux',
            name='twist_mux',
            output='screen',
            remappings={('/cmd_vel_out', LaunchConfiguration('cmd_vel_out'))},
            parameters=[twist_mux_config, {'use_sim_time': use_sim_time}],
        ),

        # Node(
        #     package='simplebot2', # Change this to your actual package name
        #     executable='laser_fixer.py',
        #     name='laser_fixer',
        #     parameters=[{'use_sim_time': True}],
        #     output='screen'
        # ),

    ])
