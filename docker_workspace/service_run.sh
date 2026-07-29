#!/bin/bash

# Remove existing container if it exists
if [ "$(docker ps -a | grep ros2)" ]; then
    docker rm -f ros2
fi

PARENT_DIR=$(dirname "$PWD")

docker run -it --network host \
    --name ros2 \
    --hostname localhost \
    --gpus all \
    --privileged \
    --shm-size=2gb \
    --user 1000:1000 \
    --group-add $(getent group dialout | cut -d: -f3) \
    --group-add $(getent group video | cut -d: -f3) \
    --group-add $(getent group alexander | cut -d: -f3) \
    --group-add $(getent group plugdev | cut -d: -f3) \
    --group-add messagebus \
    --volume "$PARENT_DIR/ros_ws/:/home/alexander/simplebot3/ros_ws/" \
    --volume "/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --volume "/etc/localtime:/etc/localtime:ro" \
    --volume "/dev:/dev" \
    --volume "/var/run/dbus:/var/run/dbus" \
    --volume "/var/run/avahi-daemon/socket:/var/run/avahi-daemon/socket" \
    --env="DISPLAY=$DISPLAY" \
    --env="XDG_RUNTIME_DIR=/tmp/runtime-alexander" \
    --env="QT_X11_NO_MITSHM=1" \
    --env="NVIDIA_VISIBLE_DEVICES=all" \
    --env="NVIDIA_DRIVER_CAPABILITIES=all" \
    --env="__NV_PRIME_RENDER_OFFLOAD=1" \
    --env="__GLX_VENDOR_LIBRARY_NAME=nvidia" \
    --env="__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json" \
    --env="OGRE_RTT_MODE=FBO" \
    --env="GZ_PARTITION=alexander_sim" \
    --env="GZ_IP=127.0.0.1" \
    --env="ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST" \
    --env="UDEV=1" \
    --env="BLINKA_MCP2221=1" \
    ros2:v0.3.1 bash
