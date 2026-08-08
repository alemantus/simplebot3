#include "simplebot_hardware/simplebot_chassis_hardware.hpp"
#include "hardware_interface/types/hardware_interface_type_values.hpp"
#include <string>
#include <vector>
#include <sstream>
#include <cmath>

namespace simplebot_hardware
{

hardware_interface::CallbackReturn SimplebotChassisHardware::on_init(
  const hardware_interface::HardwareInfo & info)
{
  if (hardware_interface::SystemInterface::on_init(info) != hardware_interface::CallbackReturn::SUCCESS)
  {
    return hardware_interface::CallbackReturn::ERROR;
  }

  port_name_ = info_.hardware_parameters.at("serial_port");
  baud_rate_ = std::stoi(info_.hardware_parameters.at("baud_rate"));

  hw_commands_.resize(info_.joints.size(), 0.0);
  hw_positions_.resize(info_.joints.size(), 0.0);
  hw_velocities_.resize(info_.joints.size(), 0.0);

  for (const auto & joint : info_.joints)
  {
    if (joint.command_interfaces.empty() || joint.command_interfaces[0].name != hardware_interface::HW_IF_VELOCITY)
    {
      RCLCPP_FATAL(rclcpp::get_logger("SimplebotChassisHardware"), "Joint %s requires velocity command interface.", joint.name.c_str());
      return hardware_interface::CallbackReturn::ERROR;
    }
  }

  return hardware_interface::CallbackReturn::SUCCESS;
}

std::vector<hardware_interface::StateInterface> SimplebotChassisHardware::export_state_interfaces()
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

std::vector<hardware_interface::CommandInterface> SimplebotChassisHardware::export_command_interfaces()
{
  std::vector<hardware_interface::CommandInterface> command_interfaces;
  for (size_t i = 0; i < info_.joints.size(); i++)
  {
    command_interfaces.emplace_back(hardware_interface::CommandInterface(
      info_.joints[i].name, hardware_interface::HW_IF_VELOCITY, &hw_commands_[i]));
  }
  return command_interfaces;
}

hardware_interface::CallbackReturn SimplebotChassisHardware::on_activate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  RCLCPP_INFO(rclcpp::get_logger("SimplebotChassisHardware"), "Connecting to serial port %s at %d...", port_name_.c_str(), baud_rate_);
  if (!serial_.connect(port_name_, baud_rate_))
  {
    RCLCPP_ERROR(rclcpp::get_logger("SimplebotChassisHardware"), "Failed to open serial port %s.", port_name_.c_str());
    return hardware_interface::CallbackReturn::ERROR;
  }
  RCLCPP_INFO(rclcpp::get_logger("SimplebotChassisHardware"), "Chassis serial interface successfully activated.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::CallbackReturn SimplebotChassisHardware::on_deactivate(
  const rclcpp_lifecycle::State & /*previous_state*/)
{
  serial_.write_string("0,0,0,0\n");
  serial_.disconnect();
  RCLCPP_INFO(rclcpp::get_logger("SimplebotChassisHardware"), "Chassis serial interface deactivated.");
  return hardware_interface::CallbackReturn::SUCCESS;
}

hardware_interface::return_type SimplebotChassisHardware::read(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & period)
{
  if (!serial_.is_open()) return hardware_interface::return_type::ERROR;

  std::string response = serial_.read_line();
  if (response.empty()) return hardware_interface::return_type::OK;

  std::stringstream ss(response);
  double fl_rps, fr_rps, rl_rps, rr_rps;
  if (ss >> fl_rps >> fr_rps >> rl_rps >> rr_rps)
  {
    double conversion = 2.0 * M_PI;

    hw_velocities_[0] = fl_rps * conversion;
    hw_velocities_[1] = fr_rps * conversion;
    hw_velocities_[2] = rl_rps * conversion;
    hw_velocities_[3] = rr_rps * conversion;

    double dt = period.seconds();
    for (size_t i = 0; i < info_.joints.size() && i < 4; i++) {
      hw_positions_[i] += hw_velocities_[i] * dt;
    }
  }

  return hardware_interface::return_type::OK;
}

hardware_interface::return_type SimplebotChassisHardware::write(
  const rclcpp::Time & /*time*/, const rclcpp::Duration & /*period*/)
{
  if (!serial_.is_open()) return hardware_interface::return_type::ERROR;

  double conversion = 1.0 / (2.0 * M_PI);
  double fl_rps = hw_commands_[0] * conversion;
  double fr_rps = hw_commands_[1] * conversion;
  double rl_rps = hw_commands_[2] * conversion;
  double rr_rps = hw_commands_[3] * conversion;

  std::stringstream cmd;
  cmd << fl_rps << "," << fr_rps << "," << rl_rps << "," << rr_rps << "\n";
  serial_.write_string(cmd.str());

  return hardware_interface::return_type::OK;
}

} // namespace simplebot_hardware

#include "pluginlib/class_list_macros.hpp"
PLUGINLIB_EXPORT_CLASS(
  simplebot_hardware::SimplebotChassisHardware, hardware_interface::SystemInterface)
