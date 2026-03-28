# Simplebot 3

simplebot2 had become a clutter of learning mistakes, for example instead of using ros2 control I wrote my own setup which worked but made everything miserable. Using nav2 for example where held together using the software equivalent of ducktape, and using gazebo were downright impossible. Hence simplebot 3 is the project where i focus on doing things the right (or righter) way. Starting with implementing ros2_control and simplebot_description so that I can implement new features in gazebo first, get everything to work with all the comforts of simulated environments, and then transfer that to the real robot.

## So what works?

Currently I have the following up and running

- Gazebo environment
  - Mecanum drive plug-in
  - Orbbec femto bolt camera
  - Roarm moveit

- URDF descriptions
  - Of Helene (the robot)
  - Orbbec femto bolt camera
  - Of the roarm2
- MoveIt2 for the roarm
- Nav2
