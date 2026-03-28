#!/bin/python3

import evdev
from evdev import InputDevice, categorize, ecodes
import subprocess
import time

#subprocess.run(["docker", "container", "rm", "-f", "ros2"])

# Specify the device (event9 in this case)
device_path = '/dev/input/event9'

# Initialize the button states
button_states = {}

button_states = {
    ecodes.BTN_NORTH: 0,  # Replace "code_1", etc., with actual event codes
    ecodes.BTN_SOUTH: 0,
    ecodes.BTN_EAST: 0,
    ecodes.BTN_WEST: 0,
}

def start_ros2_nav2():
    subprocess.run(["bash", "/home/alexander/simplebot2/docker_workspace/ros2_run.sh", "use_nav:=true", "use_nav2_wo_amcl:=false", "use_slam:=false"])  # Replace with actual command
    time.sleep(0.1)

def start_ros2_slam():
    subprocess.run(["bash", "/home/alexander/simplebot2/docker_workspace/ros2_run.sh", "use_nav:=false", "use_nav2_wo_amcl:=false", "use_slam:=true"])  # Replace with actual command
    time.sleep(0.1)

def start_ros2_nav2_wo_amcl():
    subprocess.run(["bash", "/home/alexander/simplebot2/docker_workspace/ros2_run.sh", "use_nav:=false", "use_nav2_wo_amcl:=true", "use_slam:=true"])  # Replace with actual command
    time.sleep(0.1)


def stop_ros2():
    subprocess.run(["bash", "/home/alexander/simplebot2/docker_workspace/ros2_stop_nodes.sh"])
    time.sleep(1)
    subprocess.run(["docker", "container", "rm", "-f", "ros2"])  # Replace with actual command
    time.sleep(0.1)

device = InputDevice(device_path)

# Listen for events
for event in device.read_loop():
    if event.type == ecodes.EV_KEY:  # Event type 1 (EV_KEY)
        if event.code in button_states:  # Only track relevant buttons
            button_states[event.code] = event.value  # Update the button state


            # Check if both buttons are pressed
            if button_states[ecodes.BTN_SOUTH] == 1 and button_states[ecodes.BTN_NORTH] == 0:
                print("ros2 start")
                start_ros2_nav2()
                time.sleep(1)

            # Check if both buttons are pressed
            elif button_states[ecodes.BTN_EAST] == 1 and button_states[ecodes.BTN_NORTH] == 0:
                print("ros2 start")
                start_ros2_slam()
                time.sleep(1)

            # Check if both buttons are pressed
            # this is the one for moving around and mapping, pressing buttons to save and move towards goal
            elif button_states[ecodes.BTN_WEST] == 1 and button_states[ecodes.BTN_NORTH] == 0:
                print("ros2 start")
                start_ros2_nav2_wo_amcl()
                time.sleep(1)



            # Check if both buttons are pressed
            elif button_states[ecodes.BTN_SOUTH] == 1 and button_states[ecodes.BTN_NORTH] == 1:
                print("Both buttons pressed")
                stop_ros2()
                time.sleep(1)

