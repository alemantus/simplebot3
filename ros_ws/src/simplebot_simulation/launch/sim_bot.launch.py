#!/usr/bin/env python3
from better_launch import BetterLaunch, launch_this
from ament_index_python.packages import get_package_share_directory
from pathlib import Path
import os
import tempfile
import sys

# Force short ROS log filenames
os.environ["ROS_LOG_DIR"] = tempfile.gettempdir()


@launch_this(ui=True)
def sim_bot():

    robot_name="simplebot"
    world_file="empty.world"
    log_level="info"
    use_sim_time=True
    use_robot_state_pub=True
    use_nav2=True
    use_nav2_slam=True
    use_rviz=True
    use_gazebo=True
    load_controllers=True
    headless=False
    jsp_gui=False
    enable_odom_tf=True

    x=2.5
    y=2.5
    z=0.05
    roll=0.0
    pitch=0.0
    yaw=0.0
    
    sys.argv = [sys.argv[0]]  # Clean argv for better_launch
    print("Launch function running")

    bl = BetterLaunch()

    # Package paths
    pkg_simulation = Path(get_package_share_directory("simplebot_simulation"))
    pkg_description = Path(get_package_share_directory("simplebot_description"))
    pkg_bot2 = Path(get_package_share_directory("simplebot2"))
    pkg_misc = Path(get_package_share_directory("misc"))
    pkg_nav2 = Path(get_package_share_directory("nav2_bringup"))

    world_path = pkg_simulation / "worlds" / world_file
    gz_bridge_config = pkg_simulation / "config" / "ros_gz_bridge.yaml"
    default_rviz_path = pkg_simulation / "rviz" / "yahboom_rosmaster_gazebo_sim.rviz"

    # Set Gazebo resource path
    os.environ["GZ_SIM_RESOURCE_PATH"] = str(pkg_description.parent)

    # ----------------------
    # Robot state publisher
    # ----------------------
    if use_robot_state_pub:
        bl.include(
            package="simplebot_description",
            launchfile="robot_state_publisher.launch.py",
            enable_odom_tf=enable_odom_tf,
            jsp_gui=jsp_gui,
            rviz_config_file=str(default_rviz_path),
            use_rviz=use_rviz,
            use_gazebo=use_gazebo,
            use_sim_time=use_sim_time,
        )

    # ----------------------
    # SLAM
    # ----------------------
    if use_nav2_slam:
        bl.include(
            package="simplebot2",
            launchfile="online_async_launch.py",
            use_sim_time=use_sim_time,
            log_level=log_level,
            autostart=True,
            use_lifecycle_manager=False,
        )

    # ----------------------
    # Navigation
    # ----------------------
    if use_nav2:
        bl.include(
            package="nav2_bringup",
            launchfile="navigation_launch.py",
            use_sim_time=use_sim_time,
            autostart=True,
            params_file=str(pkg_nav2 / "params" / "nav2_params.yaml"),
            use_lifecycle_manager=True,
            log_level=log_level,
        )

        bl.include(
            package="misc",
            launchfile="joy2pose_launch.py",
            log_level=log_level,
        )

    # ----------------------
    # Controllers
    # ----------------------
    if load_controllers:
        bl.include(
            package="simplebot_description",
            launchfile="load_ros2_controllers.launch.py",
            use_sim_time=use_sim_time,
        )

    # ----------------------
    # Gazebo server & GUI
    # ----------------------
    bl.include(
        package="ros_gz_sim",
        launchfile="gz_sim.launch.py",
        gz_args=f"-r -s {world_path}",
    )

    if not headless:
        bl.include(
            package="ros_gz_sim",
            launchfile="gz_sim.launch.py",
            gz_args="-g",
        )

    # ----------------------
    # ROS-GZ bridge
    # ----------------------
    bl.node(
        package="ros_gz_bridge",
        executable="parameter_bridge",
        name="gz_bridge",
        params={
            "config_file": str(gz_bridge_config),
            "use_sim_time": use_sim_time,
        },
    )

    # ----------------------
    # Image bridge
    # ----------------------
    # Use a namespace group instead of extra_arguments for topic remap
    with bl.group("cam_1"):
        bl.node(
            package="ros_gz_image",
            executable="image_bridge",
            name="gz_image_bridge",
            params={"use_sim_time": use_sim_time},
        )

    # ----------------------
    # Spawn robot
    # ----------------------
    # Instead of CLI arguments, pass via parameters or call a spawn service if supported
    bl.node(
        package="ros_gz_sim",
        executable="create",
        name="spawn_robot",
        params={
            "robot_name": robot_name,
            "topic": "robot_description", # <--- This is the key "geometry" parameter
            "x": x,
            "y": y,
            "z": z,
            "roll": roll,
            "pitch": pitch,
            "yaw": yaw,
        },
    )

