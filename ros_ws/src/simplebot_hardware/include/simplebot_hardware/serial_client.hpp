#pragma once

#include <boost/asio.hpp>
#include <string>
#include <iostream>

namespace simplebot_hardware
{
class SerialClient
{
public:
  SerialClient() : io_(), port_(io_) {}

  ~SerialClient()
  {
    disconnect();
  }

  bool connect(const std::string & port_name, unsigned int baud_rate)
  {
    try {
      if (port_.is_open()) {
        port_.close();
      }
      port_.open(port_name);
      port_.set_option(boost::asio::serial_port_base::baud_rate(baud_rate));
      port_.set_option(boost::asio::serial_port_base::character_size(8));
      port_.set_option(boost::asio::serial_port_base::parity(boost::asio::serial_port_base::parity::none));
      port_.set_option(boost::asio::serial_port_base::stop_bits(boost::asio::serial_port_base::stop_bits::one));
      port_.set_option(boost::asio::serial_port_base::flow_control(boost::asio::serial_port_base::flow_control::none));
      return true;
    } catch (const std::exception & e) {
      std::cerr << "Serial port error: " << e.what() << std::endl;
      return false;
    }
  }

  void disconnect()
  {
    if (port_.is_open()) {
      boost::system::error_code ec;
      port_.close(ec);
    }
  }

  bool is_open() const { return port_.is_open(); }

  void write_string(const std::string & s)
  {
    if (!is_open()) return;
    boost::system::error_code ec;
    boost::asio::write(port_, boost::asio::buffer(s.c_str(), s.size()), ec);
  }

  std::string read_line()
  {
    if (!is_open()) return "";

    char c;
    std::string line = "";
    boost::system::error_code ec;

    while (true) {
      size_t n = boost::asio::read(port_, boost::asio::buffer(&c, 1), ec);
      if (ec || n == 0) break;
      if (c == '\n') break;
      if (c != '\r') {
        line += c;
      }
    }
    return line;
  }

private:
  boost::asio::io_service io_;
  boost::asio::serial_port port_;
};
}
