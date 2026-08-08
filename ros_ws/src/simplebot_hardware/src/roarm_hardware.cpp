#include "simplebot_hardware/roarm_hardware.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include <string>
#include <vector>
#include <sstream>
#include <cmath>

namespace simplebot_hardware
{

hardware_interface::CallbackReturn RoArmHardware::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) != hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  port_name_ = info_.hardware_parameters.at("serial_port");
  baud_rate_ = std::stoi(info_.hardware_parameters.at("baud_rate"));

  hw_positions_.resize(info_.joints.size(), 0.0);
  hw_velocities_.resize(info_.joints.size(), 0.0);

  // Count only actuated (non-mimic) joints for command slots.
  size_t cmd_count = 0;
  for (const auto & joint : info_.joints)
  {
    bool is_mimic = joint.parameters.count("mimic") > 0;
    if (!is_mimic)
    {
      if (joint.command_interfaces.empty() ||
          joint.command_interfaces[0].name != hardware_interface::HW_IF_POSITION)
      {
        RCLCPP_FATAL(rclcpp::get_logger("RoArmHardware"),
          "Actuated joint %s requires a position command interface.", joint.name.c_str());
        return hardware_interface::CallbackReturn::ERROR;
      }
      cmd_count++;
    }
  }
  hw_commands_.resize(cmd_count, 0.0);

  return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> RoArmHardware::export_state_interfaces()
{
  std::vector<hardware_interface::StateInterface> state_interfaces;
  for (size_t i = 0; i < info_.joints.size(); i++)
  {
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      info_.joints[i].name, hardware_interface::HW_IF_POSITION, &hw_positions_[i]));
    state_interfaces.emplace_back(hardware_interface::StateInterface(
      info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &hw_velocities_[i]));
  }
  return state_interfaces;
}

std::vector<hardware_interface::CommandInterface> RoArmHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;
  size_t cmd_idx = 0;
  for (size_t i = 0; i < info_.joints.size(); i++)
  {
    bool is_mimic = info_.joints[i].parameters.count("mimic") > 0;
    if (!is_mimic)
    {
      command_interfaces.emplace_back(hardware_interface::CommandInterface(
        info_.joints[i].name, hardware_interface::HW_IF_POSITION, &hw_commands_[cmd_idx++]));
    }
  }
  return command_interfaces;
}

hardware_interface::CallbackReturn RoArmHardware::on_activate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(rclcpp::get_logger("RoArmHardware"), "Connecting to arm serial port %s at %d...", port_name_.c_str(), baud_rate_);
  if (!serial_.connect(port_name_, baud_rate_))
  {
    RCLCPP_ERROR(rclcpp::get_logger("RoArmHardware"), "Failed to open arm serial port %s.", port_name_.c_str());
    return hardware_interface::CallbackReturn::ERROR;
  }
  RCLCPP_INFO(rclcpp::get_logger("RoArmHardware"), "Arm serial interface successfully activated.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn RoArmHardware::on_deactivate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  serial_.disconnect();
  RCLCPP_INFO(rclcpp::get_logger("RoArmHardware"), "Arm serial interface deactivated.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type RoArmHardware::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  if (!serial_.is_open()) return hardware_interface::return_type::ERROR;

  serial_.write_string("{\"T\":101}\n");

  std::string response = serial_.read_line();
  if (response.empty()) return hardware_interface::return_type::OK;

  try {
    size_t base_pos = response.find("\"base\":");
    size_t shoulder_pos = response.find("\"shoulder\":");
    size_t elbow_pos = response.find("\"elbow\":");
    size_t wrist_pos = response.find("\"wrist\":");
    size_t roll_pos = response.find("\"roll\":");
    size_t hand_pos = response.find("\"hand\":");

    if (base_pos != std::string::npos && shoulder_pos != std::string::npos)
    {
      if (hw_positions_.size() > 0) hw_positions_[0] = std::stod(response.substr(base_pos + 7, response.find(",", base_pos) - (base_pos + 7)));
      if (hw_positions_.size() > 1) hw_positions_[1] = std::stod(response.substr(shoulder_pos + 11, response.find(",", shoulder_pos) - (shoulder_pos + 11)));
      if (hw_positions_.size() > 2) hw_positions_[2] = std::stod(response.substr(elbow_pos + 8, response.find(",", elbow_pos) - (elbow_pos + 8)));
      if (hw_positions_.size() > 3) hw_positions_[3] = std::stod(response.substr(wrist_pos + 8, response.find(",", wrist_pos) - (wrist_pos + 8)));
      if (hw_positions_.size() > 4) hw_positions_[4] = std::stod(response.substr(roll_pos + 7, response.find(",", roll_pos) - (roll_pos + 7)));

      if (hand_pos != std::string::npos && hw_positions_.size() > 5) {
        hw_positions_[5] = std::stod(response.substr(hand_pos + 7, response.find("}", hand_pos) - (hand_pos + 7)));
      }
    }
  } catch (...) {
    // Skip invalid parsing frame
  }

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type RoArmHardware::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  if (!serial_.is_open()) return hardware_interface::return_type::ERROR;

  std::stringstream json;
  json << "{\"T\":102,"
       << "\"base\":" << (hw_commands_.size() > 0 ? hw_commands_[0] : 0.0) << ","
       << "\"shoulder\":" << (hw_commands_.size() > 1 ? hw_commands_[1] : 0.0) << ","
       << "\"elbow\":" << (hw_commands_.size() > 2 ? hw_commands_[2] : 0.0) << ","
       << "\"wrist\":" << (hw_commands_.size() > 3 ? hw_commands_[3] : 0.0) << ","
       << "\"roll\":" << (hw_commands_.size() > 4 ? hw_commands_[4] : 0.0) << ","
       << "\"hand\":" << (hw_commands_.size() > 5 ? hw_commands_[5] : 0.0)
       << "}\n";

  serial_.write_string(json.str());
  return hardware_interface::return_type::OK;
}

} // namespace simplebot_hardware

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(
  simplebot_hardware::RoArmHardware, hardware_interface::SystemInterface)
