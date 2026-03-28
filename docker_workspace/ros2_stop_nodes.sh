#!/bin/bash
# Get a list of all lifecycle nodes


pids=$(docker exec ros2 bash -c "source /opt/ros/jazzy/setup.sh && ps aux | grep 'ros2' | grep -v 'grep' | awk '{print \$2}'")


# Send the shutdown signal to each node
for pid in $pids; do
  echo $pid 
  docker exec ros2 bash -c "kill -SIGTERM $pid"
done

