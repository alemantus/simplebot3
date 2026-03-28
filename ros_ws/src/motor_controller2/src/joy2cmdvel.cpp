#include "rclcpp/rclcpp.hpp"
#include "sensor_msgs/msg/joy.hpp"
#include "geometry_msgs/msg/twist.hpp"

class JoyToCmdVel : public rclcpp::Node
{
public:
    JoyToCmdVel() : Node("joy_to_cmd_vel")
    {
        subscription_ = this->create_subscription<sensor_msgs::msg::Joy>(
            "joy", 10, std::bind(&JoyToCmdVel::joy_callback, this, std::placeholders::_1));
        publisher_ = this->create_publisher<geometry_msgs::msg::Twist>("/input/joystick", 10);
    }

private:
    void joy_callback(const sensor_msgs::msg::Joy::SharedPtr msg)
    {
        auto twist_msg = std::make_shared<geometry_msgs::msg::Twist>();
        twist_msg->linear.x = msg->axes[1];   // Assuming forward/backward control
        twist_msg->linear.y = msg->axes[0];  // Assuming left/right control

        float rotation_z = 0.0;
        float rotation_z_left = msg->axes[4];
        float rotation_z_right = msg->axes[5];

        // Map rotation_z_left and rotation_z_right from range [-1, 1] to [0, 1]
        rotation_z_left = (rotation_z_left + 1) / 2;
        rotation_z_right = (rotation_z_right + 1) / 2;

        if (rotation_z_right-rotation_z_left != 0){
            rotation_z = (rotation_z_right-rotation_z_left);
        }
        else{
            rotation_z = 0;
        }
        twist_msg->angular.z = rotation_z*2.5;
        publisher_->publish(*twist_msg);
    }

    rclcpp::Subscription<sensor_msgs::msg::Joy>::SharedPtr subscription_;
    rclcpp::Publisher<geometry_msgs::msg::Twist>::SharedPtr publisher_;
};

int main(int argc, char *argv[])
{
    rclcpp::init(argc, argv);
    auto node = std::make_shared<JoyToCmdVel>();
    rclcpp::spin(node);
    rclcpp::shutdown();
    return 0;
}
