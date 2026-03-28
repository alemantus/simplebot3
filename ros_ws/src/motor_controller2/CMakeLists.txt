cmake_minimum_required(VERSION 3.5)
project(motor_controller2)

# Default to C++14
if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 14)
endif()

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# Find dependencies
find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rclcpp REQUIRED)
find_package(sensor_msgs REQUIRED)  # Add this line
find_package(rclpy REQUIRED)
find_package(nav_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2_ros REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(geometry_msgs REQUIRED)

# Include Cpp "include" directory
include_directories(include)

# Define the executable name variable
set(EXECUTABLE_NAME "joy2vel")

# Create the C++ executable
add_executable(${EXECUTABLE_NAME} src/joy2cmdvel.cpp)

# Set dependencies for the executable
ament_target_dependencies(${EXECUTABLE_NAME}
    rclcpp
    sensor_msgs
)

# Install the C++ executable
install(TARGETS
  ${EXECUTABLE_NAME}
  DESTINATION lib/${PROJECT_NAME}
)

# Install Python modules
ament_python_install_package(${PROJECT_NAME})

# Install Python executables
install(PROGRAMS
  scripts/kinematics2serial.py
  scripts/odom.py
  DESTINATION lib/${PROJECT_NAME}
)

install(
  DIRECTORY launch config
  DESTINATION share/${PROJECT_NAME}
)

ament_package()
