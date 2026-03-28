FROM ros:jazzy-ros-base

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ARG USERNAME=alexander
ARG UID=1000
ARG GID=1000
ENV VIRTUAL_ENV=/home/$USERNAME/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"



# Update packages and install basic tools
RUN apt-get update && \
    apt-get install -y sudo curl lsb-release gnupg software-properties-common \
    apt-utils net-tools avahi-utils libusb-1.0-0-dev libudev-dev build-essential && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Install Python 3.10
RUN add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update --fix-missing && \
    apt-get install -y python3 python3-venv python3-dev python3-pip

#     update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1 && \
#     python3 --version && \
#     python3 -m pip install --upgrade --no-cache-dir pip setuptools wheel --ignore-installed


RUN sudo apt install avahi-utils -y
RUN sudo apt install apt-utils -y 
# Install ROS 2 packages
RUN apt-get update && \
    apt-get install -y \
    ros-dev-tools \
    ros-jazzy-rmw-cyclonedds-cpp \
    ros-jazzy-ros2-control \
    ros-jazzy-ros2-controllers \
    ros-jazzy-controller-interface \
    ros-jazzy-hardware-interface \
    ros-jazzy-realtime-tools \
    ros-jazzy-ros2-control-test-assets \
    ros-jazzy-backward-ros \
    ros-jazzy-generate-parameter-library \
    ros-jazzy-pluginlib \
    ros-jazzy-rcpputils \
    ros-jazzy-tf2 \
    ros-jazzy-tf2-msgs \
    ros-jazzy-geometry-msgs \
    ros-jazzy-nav-msgs \
    ros-jazzy-pal-statistics-msgs \
    ros-jazzy-rclcpp \
    ros-jazzy-rclcpp-lifecycle \
    ros-jazzy-ament-cmake-gmock \
    ros-jazzy-controller-manager \
    ros-jazzy-hardware-interface-testing \
    ros-jazzy-navigation2 \
    ros-jazzy-nav2-bringup \
    ros-jazzy-robot-state-publisher \
    ros-jazzy-joint-state-publisher-gui \
    ros-jazzy-xacro \
    ros-jazzy-robot-localization \
    ros-jazzy-geographic-msgs \
    ros-jazzy-rosbridge-suite \
    ros-jazzy-rosapi \
    ros-jazzy-rviz2 \
    ros-jazzy-ros-gz* \
    ros-jazzy-gz-ros2-control \
    ros-jazzy-gazebo-msgs \
    ros-jazzy-nav2-waypoint-follower \
    python3-tornado \
    python3-pil \
    python3-bson \
    python3-click \
    python3-docstring-parser \
    python3-osrf-pycommon \
    python3-setproctitle \
    python3-prompt-toolkit \
    ros-jazzy-twist-mux \
    ros-jazzy-moveit-*
#&& \

#    apt-get clean && rm -rf /var/lib/apt/lists/*

# Remove unwanted OpenCV packages
# RUN apt-get purge -y '*opencv*'

# Create user and set permissions
RUN usermod -l $USERNAME ubuntu && \
    groupmod -n $USERNAME $(id -gn 1000) && \
    usermod -d /home/$USERNAME -m $USERNAME && \
    echo "$USERNAME ALL=(ALL:ALL) NOPASSWD:ALL" > /etc/sudoers.d/$USERNAME && \
    chmod 0440 /etc/sudoers.d/$USERNAME

USER $USERNAME
WORKDIR /home/$USERNAME

# Create Python 3.10 virtual environment
RUN python3 -m venv $VIRTUAL_ENV
COPY ./requirements.txt /home/$USERNAME/requirements.txt
RUN $VIRTUAL_ENV/bin/pip install --no-cache-dir -r /home/$USERNAME/requirements.txt
RUN $VIRTUAL_ENV/bin/pip install --break-system-packages pillow

# Set up ROS 2 workspace
WORKDIR /home/$USERNAME/simplebot3/ros_ws
RUN echo "source /opt/ros/jazzy/install/setup.bash" >> /home/$USERNAME/.bashrc
RUN echo "source /opt/ros/jazzy/setup.bash" >> /home/$USERNAME/.bashrc
RUN echo "source /home/$USERNAME/simplebot3/ros_ws/install/setup.bash" >> /home/$USERNAME/.bashrc

# Add entrypoint
ADD ros-entrypoint.sh /ros-entrypoint.sh
RUN sudo apt update && sudo apt upgrade -y
RUN sudo apt-get install libnvidia-egl-wayland1 -y
ENTRYPOINT ["/ros-entrypoint.sh"]
