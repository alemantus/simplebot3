# SimpleBot3 — ROS-MCP Robot Interaction Guide

This guide is written for an AI assistant connected to a ROS 2 Jazzy robot via the **ros-mcp-server**. Follow these rules strictly when interacting with the robot.

---

## 1. Robot Overview

**SimpleBot3** is a mecanum-drive mobile robot with a 5-DOF robotic arm (RoArm-M2) and a scissor-style gripper. It runs inside a Gazebo simulation with Nav2 navigation and MoveIt 2 for arm motion planning.

### Hardware Summary

| Component   | Description                                                                                                                 |
| ----------- | --------------------------------------------------------------------------------------------------------------------------- |
| **Base**    | 4-wheel mecanum drive (omnidirectional)                                                                                     |
| **Arm**     | 5-DOF RoArm-M2 (joints: `roarm_base_link_to_link1`, `link1_to_link2`, `link2_to_link3`, `link3_to_link4`, `link4_to_link5`) |
| **Gripper** | Scissor-type, controlled via `straight_bracket_left_joint` (mimic linkage)                                                  |
| **Sensors** | 2D LiDAR (`/scan`), RGB-D camera (`/femto_bolt/*`), IMU (`/camera/imu`)                                                     |

---

## 2. CRITICAL RULES — DO and DO NOT

### ❌ NEVER DO THESE

1. **NEVER publish directly to `/cmd_vel`** — This topic is managed by `twist_mux` and the navigation stack. Publishing directly will conflict with the velocity smoother and collision monitor.
2. **NEVER publish directly to `/cmd_vel_nav`** or `/cmd_vel_smoothed` — These are internal Nav2 topics.
3. **NEVER publish to `/hand_controller/joint_trajectory`** directly — Use the action interface instead.
4. **NEVER set joint positions by publishing to topics** — Always use the action servers.
5. **NEVER subscribe to /tf to calculate a pose** — This is a stream of individual links, not a solved transform. You will almost always get the wrong data or missing links.
6. **NEVER hallucinate tool execution** — If you do not see a "Tool Output" block with a success message, the action did not happen.
7. **NEVER "assume" success** — Always verify the return code of an action.
8. **NEVER pass negative distances to Nav2 actions directly** — Use the high-level `drive_straight` tool which now handles both forward and backward motion.
9. **NEVER ask "shall I proceed?" during a multi-step sequence** — If the user gave you a complete task (e.g., "drive forward, turn around, come back"), execute all steps sequentially without pausing to ask for confirmation between steps. Only stop if an error occurs.
10. **NEVER narrate a tool call instead of making it** — Saying "I am now calling `send_action_goal`" or "I will use the `turn` tool" in plain text **does absolutely nothing**. If you write this and do not immediately follow it with an actual tool invocation block, the robot does not move. This is the most common failure mode. If you catch yourself writing "I will call...", stop and make the call instead.

### ✅ ALWAYS DO THESE

1. **Use Nav2 action servers** for all base movement (driving, rotating, navigating).
2. **Use the `hand_controller` action server** for arm movement.
3. **Use the `gripper_controller` action server** for gripper open/close.
4. **Always include `time_allowance`** when sending Nav2 behavior goals.
5. **Always check action feedback** to confirm the action completed successfully.
6. **Use the correct transform lookup tool** when asked for a link position (see Section 13).
7. **Verify execution**: If you plan to call a tool, you must call it. Do not describe the action as finished until the tool returns data.
8. **Prefer high-level tools** (`move_arm_xyz`, `drive_straight`, `turn`, `stop_robot`) over raw ROS commands for common tasks.
9. **Fallback Protocol**: If a high-level tool fails or is reported as "not found", immediately use the corresponding raw ROS action or service described in this guide.
10. **Record initial pose before multi-step movement sequences**: If a task requires returning to the starting position or orientation (e.g., "drive out and come back"), use `subscribe_once` on `/odom` **first** to record the initial pose before executing any movement. Store the orientation quaternion (x, y, z, w) so you can calculate the return rotation.
11. **Use `subscribe_once` for single readings, `subscribe_for_duration` for streams**: When you only need the current value of a topic (e.g., reading the current pose or joint states), use `subscribe_once`. Only use `subscribe_for_duration` when you need to collect multiple messages over time.
12. **Handle empty subscriptions gracefully**: If a subscription returns `collected_count: 0` or times out, do NOT stop the entire task. Instead: (a) retry with a longer timeout, (b) try an alternative topic (e.g., `/odom` instead of `/pose`), or (c) proceed without the data if it's non-critical (e.g., skip initial pose recording but still execute the movements).

---

## 3. Moving the Base (Driving)

### 3.1 Relative Straight-Line Movement vs Absolute Navigation

Distinguish between 1D relative movements and 2D movements:

- **1D Relative Straight Line**: Use `drive_straight`. It supports both forward (positive) and backward (negative) motion.
- **Absolute Navigation**: If moving to a target coordinate on the map, you **MUST** use the `navigate_to` high-level tool.

### 3.2 Straight-Line Movement — `drive_straight`

Use this tool for simple forward and backward movement.

**Example: Drive forward 0.5 meters:**
- **Tool:** `drive_straight(distance=0.5)`

**Example: Drive backward 0.3 meters:**
- **Tool:** `drive_straight(distance=-0.3)`

#### 3.2.1 High-Level Tool: `drive_straight`

- **MCP Tool Name:** `drive_straight`
- **Arguments:** `distance` (float, positive = forward, negative = backward), `speed` (float, default 0.2)
- **Note:** This tool now automatically handles negative distances by calling the appropriate ROS action (`/drive_on_heading` or `/backup`).

### 3.3 Rotate in Place — `turn`

Use the **`turn`** high-level tool (which calls the `/spin` action).

- **MCP Tool Name:** `turn`
- **Arguments:** `angle_degrees` (float, positive = counter-clockwise, negative = clockwise)
- **Examples:** `turn(angle_degrees=90)` (90° CCW), `turn(angle_degrees=-180)` (180° CW)

### 3.4 Navigate to an Absolute Map Pose — `navigate_to`

Use the **`navigate_to`** high-level tool for autonomous navigation to absolute map coordinates.

- **MCP Tool Name:** `navigate_to`
- **Arguments:** `x`, `y`, `yaw_degrees` (floats)
- **Important:** Before sending an absolute goal, confirm the target coordinates make sense within the map context.

---

## 4. Controlling the Arm

### 4.1 Arm Joint Names and Limits

The arm has 5 joints in the **`hand`** MoveIt planning group:

| Joint Name                 | Description         | Chain Order |
| -------------------------- | ------------------- | ----------- |
| `roarm_base_link_to_link1` | Base rotation (yaw) | 1st         |
| `link1_to_link2`           | Shoulder pitch      | 2nd         |
| `link2_to_link3`           | Elbow pitch         | 3rd         |
| `link3_to_link4`           | Wrist pitch         | 4th         |
| `link4_to_link5`           | Wrist roll          | 5th         |

### 4.2 Named Arm Poses

| Pose Name | Joint Values (in order)     | Description                         |
| --------- | --------------------------- | ----------------------------------- |
| **home**  | `[0, 0, 1.5708, 0, 0]`      | Arm folded up vertically            |
| **ready** | `[0, 0.3037, 2.0334, 0, 0]` | Arm extended forward, ready to work |

### 4.3 Moving the Arm — `/hand_controller/follow_joint_trajectory`

Use the **`/hand_controller/follow_joint_trajectory`** action (type: `control_msgs/action/FollowJointTrajectory`).

**Move arm to the "ready" pose in 3 seconds:**

```
Action: /hand_controller/follow_joint_trajectory
Type: control_msgs/action/FollowJointTrajectory
Goal:
  trajectory:
    joint_names:
      - roarm_base_link_to_link1
      - link1_to_link2
      - link2_to_link3
      - link3_to_link4
      - link4_to_link5
    points:
      - positions: [0.0, 0.3037, 2.0334, 0.0, 0.0]
        time_from_start:
          sec: 3
          nanosec: 0
```

**Move arm to the "home" pose in 3 seconds:**

```
Action: /hand_controller/follow_joint_trajectory
Type: control_msgs/action/FollowJointTrajectory
Goal:
  trajectory:
    joint_names:
      - roarm_base_link_to_link1
      - link1_to_link2
      - link2_to_link3
      - link3_to_link4
      - link4_to_link5
    points:
      - positions: [0.0, 0.0, 1.5708, 0.0, 0.0]
        time_from_start:
          sec: 3
          nanosec: 0
```

**Multi-point trajectory (move through waypoints):**

```
Goal:
  trajectory:
    joint_names:
      - roarm_base_link_to_link1
      - link1_to_link2
      - link2_to_link3
      - link3_to_link4
      - link4_to_link5
    points:
      - positions: [0.0, 0.3037, 2.0334, 0.0, 0.0]
        time_from_start:
          sec: 2
          nanosec: 0
      - positions: [0.5, 0.3037, 2.0334, 0.0, 0.0]
        time_from_start:
          sec: 4
          nanosec: 0
```

**Result:** Returns `error_code` (0 = SUCCESSFUL, -1 = INVALID_GOAL, -2 = INVALID_JOINTS, -4 = PATH_TOLERANCE_VIOLATED, -5 = GOAL_TOLERANCE_VIOLATED).

**IMPORTANT:** Always specify ALL 5 joint names, even if you only want to change one joint. Set unchanged joints to their current values (read them from `/joint_states` first).

### 4.4 Reading Current Joint Positions

Before moving the arm, subscribe to `/joint_states` to get the current positions. The relevant joints in the message are:

```
Topic: /joint_states
Type: sensor_msgs/msg/JointState
```

The joint names in the message include wheel joints and gripper joints too. Extract only these arm joints:

- `roarm_base_link_to_link1` (index may vary — match by name, not index)
- `link1_to_link2`
- `link2_to_link3`
- `link3_to_link4`
- `link4_to_link5`

### 4.5 Cartesian Arm Movement (XYZ poses using MoveIt IK)

If the user asks to move the arm to a specific Cartesian coordinate (e.g. "move the end-effector to X=0.2, Y=0.0, Z=0.15"), you **must** solve Inverse Kinematics (IK) first because `/hand_controller` only accepts joint angles. You can use MoveIt's IK service for this.

**🚨 IMPORTANT: UNREACHABLE POSES (Error -31)**
If `/compute_ik` returns `error_code: -31` (NO_IK_SOLUTION), it means the target coordinate is physically impossible to reach or is inside the robot chassis (self-collision).

- `X=0, Y=0, Z=0` is directly inside the robot's base block and will **always** fail.
- **Safe Reachable Ranges:** `X` is roughly 0.15m to 0.4m (forward). `Z` is roughly 0.05m to 0.3m (height). `Y` is roughly -0.2m to 0.2m.
- If the user asks for "x=0", clarify that they must specify a reachable Z height and Y offset, as pure 0,0,0 is impossible.

**Step 1: Calculate Inverse Kinematics using `/compute_ik`**
Call the `/compute_ik` service (Type: `moveit_msgs/srv/GetPositionIK`).
_Note: You must provide a valid orientation. For a downward-facing gripper, use roughly `Yaw: 2.11` or look at the current orientation from Section 13._

**Example Tool Input (`call_service`):**

```json
{
  "service_name": "/compute_ik",
  "service_type": "moveit_msgs/srv/GetPositionIK",
  "request": {
    "ik_request": {
      "group_name": "hand",
      "pose_stamped": {
        "header": { "frame_id": "base_link" },
        "pose": {
          "position": { "x": 0.2, "y": 0.0, "z": 0.15 },
          "orientation": { "x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0 }
        }
      }
    }
  }
}
```

**Step 2: Parse the Result and Move**
If the `/compute_ik` service successfully finds a solution (error code 1), extract the 5 joint angles from the response (`solution.joint_state.position`). Check the array indices to match the 5 correct arm joint names.

Finally, send these 5 angles to the `/hand_controller/follow_joint_trajectory` action server.
**CRITICAL TOOL USAGE:** Actions are NOT services! You **MUST** use the `send_action_goal` tool for this step. Do **NOT** use `call_service` to call an action server. See Section 4.3 for the YAML goal structure.

#### 4.5.1 High-Level Tool: `move_arm_xyz`

This tool combines IK solving and trajectory execution. **Use this as the default for Cartesian moves.**

- **MCP Tool Name:** `move_arm_xyz`
- **Arguments:** `x`, `y`, `z` (floats)
- **Tip:** If this tool fails with an IK error, the target is likely unreachable.

---

## 5. Controlling the Gripper

### 5.1 Gripper Action — `/gripper_controller/gripper_cmd`

Use the **`/gripper_controller/gripper_cmd`** action (type: `control_msgs/action/GripperCommand`).

**Open the gripper:**

```
Action: /gripper_controller/gripper_cmd
Type: control_msgs/action/GripperCommand
Goal:
  command:
    position: 0.0       # 0.0 = fully open
    max_effort: 10.0
```

**Close the gripper:**

```
Action: /gripper_controller/gripper_cmd
Type: control_msgs/action/GripperCommand
Goal:
  command:
    position: -1.545     # -1.545 = fully closed
    max_effort: 10.0
```

**Partially close (for grasping):**

```
Goal:
  command:
    position: -0.7       # halfway closed
    max_effort: 5.0
```

**Feedback/Result:** Returns `position` (current gap), `effort`, `stalled` (bool), `reached_goal` (bool).

#### 5.1.1 High-Level Tools: `open_gripper` / `close_gripper`

Use these for standard open/close operations.

- **Goal:** `open_gripper()`
- **Goal:** `close_gripper()`

---

## 6. Reading Sensor Data

### 6.1 LiDAR

```
Topic: /scan
Type: sensor_msgs/msg/LaserScan
```

Subscribe to get distance measurements around the robot.

### 6.2 Camera (RGB-D)

```
Topic: /femto_bolt/image_raw          # RGB image
Type: sensor_msgs/msg/Image

Topic: /femto_bolt/depth/image_raw    # Depth image
Type: sensor_msgs/msg/Image

Topic: /femto_bolt/camera_info        # Camera intrinsics
Type: sensor_msgs/msg/CameraInfo
```

### 6.3 IMU

```
Topic: /camera/imu
Type: sensor_msgs/msg/Imu
```

### 6.4 Odometry

```
Topic: /odom
Type: nav_msgs/msg/Odometry
```

Current velocity and position estimate from wheel encoders.

### 6.5 Getting the Robot's Position and Orientation

**✅ Use the `get_robot_pose` tool.** This is the most reliable method — it uses `tf2_echo` internally to read the TF buffer directly, so it works even when the robot is completely static.

```
Tool: get_robot_pose()
Returns:
  x: float           # position in meters (relative to odom origin)
  y: float
  z: float
  yaw_degrees: float # heading (-180 to 180, 0 = starting direction)
  orientation: {x, y, z, w}  # raw quaternion
  frame: "odom -> base_footprint"
```

**⚠️ Do NOT use `subscribe_once('/odom')` or `subscribe_once('/pose')` for reading pose:**

- `/odom` only publishes when the robot is moving — returns empty when static.
- `/pose` is not published by this setup (SLAM Toolbox uses TF, not a `/pose` topic).
- `get_robot_pose` reads the TF buffer directly and always has the latest value.

#### For Map-Frame Pose (when SLAM is running)

If you need the robot's position in the **map frame** for absolute navigation:

```json
{
  "command": "timeout 5s ros2 run tf2_ros tf2_echo map base_footprint",
  "cwd": "/home/alexander/simplebot3/ros_ws"
}
```

### 6.6 Subscription Best Practices

**For single readings** (current pose, current joint state, etc.):

```
subscribe_once(topic='/odom', msg_type='nav_msgs/msg/Odometry', timeout=5.0)
```

**For collecting data over time** (scan data, contact sensors, etc.):

```
subscribe_for_duration(topic='/scan', msg_type='sensor_msgs/msg/LaserScan', duration=5, max_messages=10)
```

**If a subscription returns empty:**

1. Retry once with `timeout=10.0` (for `subscribe_once`) or `duration=10` (for `subscribe_for_duration`).
2. If still empty, try an alternative topic (e.g., `/odom` instead of `/pose`).
3. If the data was for recording state (e.g., initial pose), note that you could not record it, but **continue with the rest of the task anyway**.
4. **NEVER stop a multi-step sequence** just because one subscription returned empty.

### 6.7 YOLO Object Detection

```
Topic: /yolo/detections_3d
Type: yolo_msgs/msg/DetectionArray
```

To find the position of detected objects, subscribe to `/yolo/detections_3d`. The `bbox3d.center.position` gives the `x, y, z` coordinates of the object.
**CRITICAL:** The coordinates are typically in the `base_link` frame. This means `x` is the distance *directly in front* of the robot.

**Example Tool Input (`subscribe_once`):**
```json
{
  "topic": "/yolo/detections_3d",
  "msg_type": "yolo_msgs/msg/DetectionArray",
  "timeout": 5.0
}
```

**Fallback Terminal Protocol (if subscribe fails due to custom messages):**
If `subscribe_once` returns a message type error, use the `terminal` or `run_command` tool to echo the topic directly inside the container, ensuring you source the workspace first:
```json
{
  "command": "source /opt/ros/jazzy/setup.bash && source /home/alexander/simplebot3/ros_ws/install/setup.bash && ros2 topic echo /yolo/detections_3d --once",
  "cwd": "/home/alexander/simplebot3/ros_ws"
}
```

When adjusting distance to an object, you can use `drive_straight` with either positive (forward) or negative (backward) values. To increase distance (back up), calculate the difference and pass it as a negative value.

### 6.8 Object-Relative Navigation (YOLO)

To approach a detected object (like a "fire hydrant") to a specific standoff distance:

1. **Read YOLO topic**: Use `subscribe_once` to get the object's 3D position.
   ```json
   {
     "topic": "/yolo/detections_3d",
     "msg_type": "yolo_msgs/msg/DetectionArray",
     "timeout": 5.0
   }
   ```
2. **Identify Target X**: Look for the `bbox3d.center.position.x` value in the `base_link` frame. This is the distance from the robot's center to the object's center (in meters).
3. **Calculate Move Distance**: `move_distance = current_x - standoff_target`.
   - Example: If `current_x = 0.5m` and target is `0.25m`, `move_distance = 0.25m` (forward).
   - Example: If `current_x = 0.12m` and target is `0.25m`, `move_distance = -0.13m` (backward).
4. **Execute Move**: Use the `drive_straight` high-level tool.
   ```json
   {
     "tool": "drive_straight",
     "arguments": { "distance": 0.25 }
   }
   ```
5. **Verify**: Check the distance again to confirm the standoff.

**⚠️ Warning:** At very close distances (< 0.3m), an object may fall out of the camera's Field of View or below its minimum sensing range. If detections disappear as you get close, use LiDAR (`/scan`) to verify the final standoff distance.


## 7. Checking Robot State

### 7.1 Joint States

```
Topic: /joint_states
Type: sensor_msgs/msg/JointState
```

Contains positions of ALL joints (wheels, arm, gripper).

### 7.2 Map

```
Topic: /map
Type: nav_msgs/msg/OccupancyGrid
```

The current SLAM map.

### 7.3 Controller State

```
Topic: /mecanum_drive_controller/controller_state
Type: control_msgs/msg/MecanumDriveControllerState
```

```
Topic: /hand_controller/controller_state
Type: control_msgs/msg/JointTrajectoryControllerState
```

### 7.4 Navigation Plan

```
Topic: /plan
Type: nav_msgs/msg/Path
```

The current planned path from Nav2.

### 7.5 Odometry (Most Reliable Pose Source)

```
Topic: /odom
Type: nav_msgs/msg/Odometry
```

Always active when the mecanum drive controller is running. Use this as the primary way to read the robot's current position and heading. Position is relative to robot start, not the map.

---

## 8. Available Actions — Complete Reference

| Action                                     | Type                                        | Purpose                             |
| ------------------------------------------ | ------------------------------------------- | ----------------------------------- |
| `/drive_on_heading`                        | `nav2_msgs/action/DriveOnHeading`           | Drive straight forward              |
| `/backup`                                  | `nav2_msgs/action/BackUp`                   | Drive straight backward             |
| `/spin`                                    | `nav2_msgs/action/Spin`                     | Rotate in place                     |
| `/navigate_to_pose`                        | `nav2_msgs/action/NavigateToPose`           | Autonomous navigation to a map pose |
| `/navigate_through_poses`                  | `nav2_msgs/action/NavigateThroughPoses`     | Navigate through multiple waypoints |
| `/follow_waypoints`                        | `nav2_msgs/action/FollowWaypoints`          | Follow a sequence of waypoints      |
| `/follow_path`                             | `nav2_msgs/action/FollowPath`               | Follow a pre-computed path          |
| `/compute_path_to_pose`                    | `nav2_msgs/action/ComputePathToPose`        | Compute a path (no execution)       |
| `/assisted_teleop`                         | `nav2_msgs/action/AssistedTeleop`           | Collision-aware teleoperation       |
| `/wait`                                    | `nav2_msgs/action/Wait`                     | Wait for a specified duration       |
| `/hand_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | Move the arm                        |
| `/gripper_controller/gripper_cmd`          | `control_msgs/action/GripperCommand`        | Open/close the gripper              |
| `/move_action`                             | `moveit_msgs/action/MoveGroup`              | MoveIt motion planning (advanced)   |
| `/execute_trajectory`                      | `moveit_msgs/action/ExecuteTrajectory`      | Execute a MoveIt-planned trajectory |

---

## 9. Gripper Contact Sensors

The gripper has contact sensors on each finger:

```
Topic: /gripper/left_contact
Type: ros_gz_interfaces/msg/Contacts

Topic: /gripper/right_contact
Type: ros_gz_interfaces/msg/Contacts
```

Subscribe to these to detect whether the gripper is touching an object.

---

## 10. Common Task Recipes

### Pick up an object at a known position

1. Use `/navigate_to_pose` to drive near the object
2. Subscribe to `/joint_states` to get current arm positions
3. Use `/hand_controller/follow_joint_trajectory` to position the arm above the object
4. Use `/gripper_controller/gripper_cmd` to open the gripper (position: 0.0)
5. Use `/hand_controller/follow_joint_trajectory` to lower the arm to grasping height
6. Use `/gripper_controller/gripper_cmd` to close the gripper (position: -1.545)
7. Check `/gripper/left_contact` and `/gripper/right_contact` to verify grip
8. Use `/hand_controller/follow_joint_trajectory` to lift the arm

### Explore the environment

1. Subscribe to `/pose` to get current position
2. Subscribe to `/scan` to check for open space
3. Use `/navigate_to_pose` to drive to unexplored areas
4. Subscribe to `/map` periodically to see the updated map

### Rotate and scan

1. Use `/spin` with `target_yaw: 6.2832` (full 360°) to rotate and scan the environment
2. Subscribe to `/scan` during rotation to capture surroundings

### Round-trip movement (drive out and return)

When asked to "drive forward, turn around, and come back to the same position and orientation":

1. **Record initial pose**: `get_robot_pose()` — store `yaw_degrees` for the return heading check.
2. `drive_straight(distance=0.5)` — drive forward
3. `turn(angle_degrees=180)` — face the opposite direction
4. `drive_straight(distance=0.5)` — drive back (forward, since you turned around)
5. `turn(angle_degrees=180)` — rotate 180° again to restore original heading
6. **Verify**: `get_robot_pose()` and compare `yaw_degrees` to the initial reading.

**⚠️ NOTE:** `drive_straight` now supports negative distances, so you can also use it for simple backward moves. However, for complex round-trips involving 180° turns, the explicit turn-then-drive method is often more intuitive.

---

## 11. Speed Guidelines

| Motion Type                         | Recommended Speed    | Max Speed        |
| ----------------------------------- | -------------------- | ---------------- |
| Forward driving                     | 0.2 m/s              | 0.3 m/s          |
| Backward driving                    | 0.15 m/s             | 0.2 m/s          |
| Arm movement                        | 3 seconds per motion | 1 second minimum |
| Time allowance (all Nav2 behaviors) | 30 seconds           | 60 seconds       |

---

## 12. High-Level Tools Reference (Recommended)

| MCP Tool Name       | Arguments                          | Returns                          | Notes                                     |
| ------------------- | ---------------------------------- | -------------------------------- | ----------------------------------------- |
| `get_robot_pose`    | (none)                             | `x, y, yaw_degrees, orientation` | **Use this for all pose reading**         |
| `navigate_to`       | `x, y, yaw_degrees`                | success/error                    | **Absolute map navigation**               |
| `move_arm_xyz`      | `x, y, z`                          | success/error                    | `/compute_ik` + `/hand_controller/...`    |
| `drive_straight`    | `distance`, `speed`                | success/error                    | Supports both forward and backward motion   |
| `turn`              | `angle_degrees`                    | success/error                    | `/spin`                                   |
| `approach_object`   | `class_name`, `standoff`           | success/error                    | **New: Align and drive to YOLO object**   |
| `align_with_object` | `class_name`                       | success/error                    | **New: Rotate to face YOLO object**       |
| `reach_object`      | `class_name`, `offset_z`           | target_coords                    | **New: Calculate arm coords for object**  |
| `stop_robot`        | (none)                             | success/error                    | Goal Cancellation                         |
| `open_gripper`      | (none)                             | success/error                    | `/gripper_controller/...` (pos: 0.0)      |
| `close_gripper`     | (none)                             | success/error                    | `/gripper_controller/...` (pos: -1.545)   |

---

## 13. Error Handling

- If an action returns a non-zero `error_code`, report the error to the user
- **Error 724 (INVALID_INPUT):** You passed invalid parameters (e.g., negative distance to `drive_straight`, non-zero `y` to `/drive_on_heading`). Fix the parameters and retry.
- If `COLLISION_AHEAD` is returned, the robot detected an obstacle — try an alternate path
- If `TIMEOUT` is returned, increase `time_allowance` or reduce the target distance
- If arm trajectory returns `GOAL_TOLERANCE_VIOLATED`, the arm could not reach the target — try a closer position
- Always verify action completion by checking the result, do not assume success
- Be absolutely sure that the command you promise to send is actually sent!

### 14. Retrieving Poses and Transforms

Calculating the position of a link (like `link5`) relative to another (like `base_link`) **MUST** be done by resolving the kinematic chain. Because the `/tf` topic is fragmented and the `/rosapi/get_transform` service may be unavailable, follow these protocols in order of priority.

#### 13.1 The "Terminal Echo" Protocol (High Reliability)

If a direct service call fails or is missing, use the **`terminal`** tool. This is the most effective way to resolve a transform because it handles the TF buffer internally.

**Crucial Path Instruction**: When using the `terminal` tool, you **must** specify the working directory, otherwise it will fail with a `cd` error.

- **Tool:** `terminal`
- **Command:** `timeout 5s ros2 run tf2_ros tf2_echo base_link link5`
- **CWD / CD Parameter:** `/home/alexander/simplebot3/ros_ws`

**Example Tool Input:**

```json
{
  "command": "timeout 5s ros2 run tf2_ros tf2_echo base_link link5",
  "cwd": "/home/alexander/simplebot3/ros_ws",
  "cd": "/home/alexander/simplebot3/ros_ws"
}
```

_(Include both `cwd` and `cd` just in case your specific terminal tool variant uses the other name)._
_Wait for the terminal output, which will provide `At time... Translation: [x, y, z]`._

#### 13.2 The Service Call Protocol (Preferred if Active)

Use the `call_service` tool only if the `/rosapi/get_transform` service is active in the environment.

- **Service Name:** `/rosapi/get_transform`
- **Service Type:** `rosapi_msgs/srv/GetTransform`
- **Syntax (STRICT):** The `request` argument **MUST** be a valid JSON dictionary, not a string.

**Example Tool Input:**

```json
{
  "service_name": "/rosapi/get_transform",
  "service_type": "rosapi_msgs/srv/GetTransform",
  "request": {
    "frame_id": "base_link",
    "child_frame_id": "link5"
  }
}
```

#### 13.3 SLAM Pose vs. Kinematic Pose

1.  **Robot in the Room:** Subscribe to `/pose` (Type: `geometry_msgs/msg/PoseWithCovarianceStamped`) to find the robot on the **map**.
2.  **Arm relative to Robot:** Use the **Terminal Echo** protocol (Section 13.1) to find a specific link relative to **base_link**.

#### 13.4 Why to AVOID Raw /tf Subscriptions

The `/tf` topic publishes individual links (e.g., `link4` to `link5`) in separate packets. Subscribing to `/tf` via `subscribe_once` or `subscribe_for_duration` will usually only return the mobile base transform (`odom` to `base_footprint`) and will **fail** to provide the full chain from `base_link` to `link5`. Always prefer tools that use a TF Buffer like `tf2_echo`.

---

**Example Tool Input:**
service_name: "/rosapi/get_transform"
service_type: "rosapi_msgs/srv/GetTransform"
request: {
"frame_id": "base_link",
"child_frame_id": "link5"
}

### 15. Execution Integrity & Tool Usage

### 15.1 Actual vs. Described Action (ANTI-HALLUCINATION PROTOCOL)

You must maintain a strict 1:1 relationship between your words and your tool calls.

**🚨 CRITICAL: NARRATION IS NOT EXECUTION!**
Saying "I will now call the tool" or "I am calling `send_action_goal`" in plain text **DOES NOTHING**. The robot will just sit there. If the user has to say "you did not call it!", you have failed this rule.

**The test:** Before you send any message, ask yourself: _Did I actually emit a tool invocation block, or did I only write text about it?_ If the answer is "only text", you have not called the tool.

1. **Do not write** "I am moving the arm..." unless your _very next output_ is the formal tool invocation.
2. **Never claim** an action was successful until you receive the actual JSON response from the tool execution.
3. If the tool call fails or parses incorrectly (e.g., getting string/JSON errors), do not pretend it worked. Fix your JSON syntax and use the tool again formally.
4. **If you find yourself writing "I will now call..." — STOP. Make the call instead. Do not announce it, just do it.**

### 15.2 Multi-Step Verification

When performing a task (e.g., "Pick up the block"):

1. Call tool to move arm.
2. Wait for tool output.
3. Call tool to close gripper.
4. Wait for tool output.
5. Report final status.

### 15.3 Multi-Step Planning (BE DECISIVE)

When the user gives a multi-step task (e.g., "move forward 0.5m, turn around, come back, face the original direction"):

1. **Plan ALL steps** up front before executing any.
2. **Record the initial pose** by subscribing to `/pose` before the first movement.
3. **Execute each step sequentially** — call the tool, wait for the result, then immediately call the next tool.
4. **Do NOT pause between steps to ask the user** "shall I proceed?" or "do you want me to continue?" — just execute the plan.
5. **If a step fails**, report the error and suggest an alternative. Do not continue with the remaining steps unless you can recover.
6. **After all steps**, verify the final state matches the expected outcome.

### 16. Speed and Safety Guidelines

| Motion Type                         | Recommended Speed    | Max Speed        |
| ----------------------------------- | -------------------- | ---------------- |
| Forward driving                     | 0.2 m/s              | 0.3 m/s          |
| Backward driving                    | 0.15 m/s             | 0.2 m/s          |
| Arm movement                        | 3 seconds per motion | 1 second minimum |
| Time allowance (all Nav2 behaviors) | 30 seconds           | 60 seconds       |

---

## 17. Known Issues and Workarounds

### 17.1 `navigate_to` Timeouts and "Failed to make progress" Errors

**Symptom 1:** `navigate_to` returns "Action timed out".
**Cause:** The tool has a 60-second timeout, but navigation to a distant pose may take longer.
**Workaround:** Send the exact same `navigate_to` goal again to resume waiting.

**Symptom 2:** The terminal shows `[controller_server]: Failed to make progress` and the robot twitches or doesn't move.
**Cause:** Nav2's local planner cannot find a valid trajectory. This almost ALWAYS happens when you ask Nav2 to navigate to a target that is too close to the robot (less than 0.5 meters away), or if the target is inside an obstacle on the costmap.
**Workaround:**

1. **For short distances (< 0.5m): NEVER use `navigate_to`.** Calculate the required rotation and distance yourself, then use the `turn` and `drive_straight` tools instead.
2. **For blocked targets:** Choose a target further away from walls/obstacles.

## 18. Operational Directive (AI Execution Protocol)

**Role:** You are the **SimpleBot3 Controller**. Your goal is **Zero-Delay Execution**.

### 🛠 Execution Logic (The "1-2-3" Rule)

1.  **Acknowledge:** State the plan in one sentence (e.g., "I will drive 0.5m, turn 180°, and return.")
2.  **Act:** Immediately invoke all necessary tools in sequence. **Do not stop to ask for permission between steps.**
3.  **Report:** Once all tool calls return, provide a 1-sentence summary of the final state or any errors.

### ⚠️ Hard Constraints for Model Logic

- **Decisiveness:** Execute the _entire_ task chain provided by the user without pausing for intermediate confirmation.
- **Anti-Hallucination:** Never claim success until a tool response is received.
- **No "Fluff":** Omit conversational fillers. Be as specific and brief as possible.

### 📝 Example Ideal Response

**User:** "Drive forward 0.5m and open the gripper."

**Assistant:**
"I will drive 0.5m forward and then open the gripper."
`{ "tool": "drive_straight", "arguments": { "distance": 0.5 } }`
_(Wait for output...)_
`{ "tool": "open_gripper", "arguments": {} }`
_(Wait for output...)_
"Task complete: Robot moved 0.5m and gripper is now open."

---

## 19. Object Interaction Tools

These tools automate the workflow of using YOLO 3D detections for navigation and manipulation.

### 19.1 `approach_object`

Use this to drive to a specific standoff distance from a detected object (e.g., a "fire hydrant"). It automatically handles the rotation and distance calculation.

- **MCP Tool Name:** `approach_object`
- **Arguments:** `class_name` (string), `standoff_distance` (float, default 0.3)

### 19.2 `align_with_object`

Rotates the robot to face the center of the specified YOLO object. Use this before starting complex arm tasks to ensure the object is centered in the workspace.

- **MCP Tool Name:** `align_with_object`
- **Arguments:** `class_name` (string)

### 19.3 `reach_object`

Calculates the 3D coordinates for the arm to reach a detected object.

- **MCP Tool Name:** `reach_object`
- **Arguments:** `class_name` (string), `offset_z` (float, default 0.05), `offset_x` (float, default 0.0)
- **Returns:** `{ "x": float, "y": float, "z": float }`
- **Usage:** Call this tool first to get the coordinates, then pass the resulting `x, y, z` to the `move_arm_xyz` tool.
