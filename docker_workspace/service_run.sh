#!/bin/bash

# Remove existing container if it exists
if [ "$(docker ps -a | grep ros2)" ]; then
    docker rm -f ros2
fi

PARENT_DIR=$(dirname "$PWD")

docker run --network host \
    --name ros2 \
    --gpus all \
    --user 1000:1000 \
    --group-add $(getent group dialout | cut -d: -f3) \
    --group-add $(getent group video | cut -d: -f3) \
    --group-add $(getent group alexander | cut -d: -f3) \
    --group-add $(getent group plugdev | cut -d: -f3) \
    --group-add=messagebus \
    --volume $PARENT_DIR/ros_ws/:/home/alexander/simplebot3/ros_ws/ \
    --env="DISPLAY=$DISPLAY" \
    --runtime=nvidia \
    --env="NVIDIA_VISIBLE_DEVICES=all" \
    --env="NVIDIA_DRIVER_CAPABILITIES=all" \
    --env="__EGL_VENDOR_LIBRARY_FILENAMES=/usr/share/glvnd/egl_vendor.d/10_nvidia.json" \
    --env="ROS_AUTOMATIC_DISCOVERY_RANGE=LOCALHOST" \
    --env="QT_X11_NO_MITSHM=1" \
    --privileged \
    --volume="/tmp/.X11-unix:/tmp/.X11-unix:rw" \
    --volume="/etc/localtime:/etc/localtime:ro" \
    --volume="/etc/timezone:/etc/timezone:ro" \
    --volume=/dev:/dev \
    --env="UDEV=1" \
    --env="BLINKA_MCP2221"=1 \
    -v /var/run/dbus:/var/run/dbus \
    -v /var/run/avahi-daemon/socket:/var/run/avahi-daemon/socket \
    -it \
    ros2:v0.3.1 bash

