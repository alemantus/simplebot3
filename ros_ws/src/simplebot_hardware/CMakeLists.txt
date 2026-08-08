cmake_minimum_required(VERSION 3.8)
project(simplebot_hardware)

if(NOT CMAKE_CXX_STANDARD)
  set(CMAKE_CXX_STANDARD 17)
endif()

find_package(ament_cmake REQUIRED)
find_package(rclcpp REQUIRED)
find_package(hardware_interface REQUIRED)
find_package(pluginlib REQUIRED)
find_package(rclcpp_lifecycle REQUIRED)

find_package(Boost REQUIRED COMPONENTS system)

add_library(simplebot_hardware SHARED
  src/simplebot_chassis_hardware.cpp
  src/roarm_hardware.cpp
)

target_include_directories(simplebot_hardware PRIVATE
  include
)

target_link_libraries(simplebot_hardware
  PRIVATE
  Boost::system
)

ament_target_dependencies(simplebot_hardware
  PUBLIC
  rclcpp
  hardware_interface
  pluginlib
  rclcpp_lifecycle
)

pluginlib_export_plugin_description_file(hardware_interface plugin.xml)

install(TARGETS simplebot_hardware
  DESTINATION lib
)

install(DIRECTORY include/
  DESTINATION include
)

ament_package()
