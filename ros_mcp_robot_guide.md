# SimpleBot3 — ROS-MCP Robot Interaction Guide

This guide is written for an AI assistant connected to a ROS 2 Jazzy robot via the **ros-mcp-server**. Follow these rules strictly when interacting with the robot.

---

## 1. Robot Overview

**SimpleBot3** is a mecanum-drive mobile robot with a 5-DOF robotic arm (RoArm-M2) and a scissor-style gripper. It runs inside a Gazebo simulation with Nav2 navigation and MoveIt 2 for arm motion planning.

### Hardware Summary
| Component | Description |
|-----------|-------------|
| **Base** | 4-wheel mecanum drive (omnidirectional) |
| **Arm** | 5-DOF RoArm-M2 (joints: `roarm_base_link_to_link1`, `link1_to_link2`, `link2_to_link3`, `link3_to_link4`, `link4_to_link5`) |
| **Gripper** | Scissor-type, controlled via `straight_bracket_left_joint` (mimic linkage) |
| **Sensors** | 2D LiDAR (`/scan`), RGB-D camera (`/femto_bolt/*`), IMU (`/camera/imu`) |

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

---

## 3. Moving the Base (Driving)

### 3.1 Relative Straight-Line Movement (1D) vs Absolute Navigation
Distinguish between 1D relative movements and 2D movements:
- **1D Relative Straight Line (Forward/Backward)**: If moving **only** forward or backward (`y = 0.0`), use the `/drive_on_heading` or `/backup` actions.
- **Combined X, Y Relative or Absolute Navigation**: If moving to a target coordinate OR simultaneously moving X and Y (e.g. "move x: 0.5 and y: 0.2"), you **MUST** use the `/navigate_to_pose` action. 

### 3.2 Drive Forward / Backward (X-Only) — `/drive_on_heading` / `/backup`
**CRITICAL LIMITATION**: The `/drive_on_heading` and `/backup` actions **ONLY** support 1D pure forward/backward motion. **`target.y` MUST ALWAYS BE `0.0`.** If you pass a non-zero `y` value, the action server will immediately return an `INVALID_INPUT` error (error code 724 or 713).

**Example: Drive forward 0.5 meters (x: 0.5, y MUST be 0.0):**
```
Action: /drive_on_heading
Type: nav2_msgs/action/DriveOnHeading
Goal:
  target:
    x: 0.5    # distance in meters (positive = forward)
    y: 0.0    # MUST BE ZERO
    z: 0.0
  speed: 0.2  # meters per second (keep between 0.1 and 0.3)
  time_allowance:
    sec: 30
    nanosec: 0
```
For pure backward movement, use **`/backup`** with `target.x` as a negative number and `target.y: 0.0`.

#### 3.2.1 High-Level Tool: `drive_straight`
Use this tool for simple forward/backward movement without manual action goals.
- **Goal:** `drive_straight(distance=0.5)` (meters, negative for backward)

### 3.3 Relative Movement involving Y (Strafe/Diagonal) or Absolute Navigation

Nav2 built-in behaviors do NOT have a relative strafing action. To move "x: 0.5 and y: 0.2" (or go to an absolute map location):
1. **Subscribe to `/pose`** to retrieve the robot's current absolute map coordinates and orientation.
2. **Calculate the new target pose** mathematically (Current Map X/Y + Relative X/Y * orientation offset). If the user provided absolute map coordinates, skip calculation.
3. **Send goal to `/navigate_to_pose`**:

```
Action: /navigate_to_pose
Type: nav2_msgs/action/NavigateToPose
Goal:
  pose:
    header:
      frame_id: "map"
    pose:
      position:
        x: [Calculated Target X]
        y: [Calculated Target Y]
        z: 0.0
      orientation:
        # Provide calculated orientation or current orientation
        x: 0.0
        y: 0.0
        z: 0.0
        w: 1.0
  behavior_tree: ""    # leave empty for default
```

**Feedback:** Returns `distance_traveled` (float32).
**Result:** Returns `error_code` (0 = success) and `total_elapsed_time`.

### 3.3 Rotate in Place — `/spin`

Use the **`/spin`** action (type: `nav2_msgs/action/Spin`) for relative rotation.

**Rotate 90 degrees counter-clockwise (π/2 radians):**
```
Action: /spin
Type: nav2_msgs/action/Spin
Goal:
  target_yaw: 1.5708   # radians (positive = counter-clockwise, negative = clockwise)
  time_allowance:
    sec: 30
    nanosec: 0
```

**Feedback:** Returns `angular_distance_traveled` (float32).

**Feedback:** Returns `angular_distance_traveled` (float32).

#### 3.3.1 High-Level Tool: `turn`
Use this tool for simple in-place rotations.
- **MCP Tool Name:** `turn`
- **Arguments:** `angle_degrees` (float)
- **Wait Duration:** This is a blocking action; wait for the tool to return a result before proceeding.

### 3.4 Navigate to an Absolute Map Pose — `/navigate_to_pose`

Use the **`/navigate_to_pose`** action (type: `nav2_msgs/action/NavigateToPose`) **ONLY** for autonomous navigation to absolute map coordinates.

```
Action: /navigate_to_pose
Type: nav2_msgs/action/NavigateToPose
Goal:
  pose:
    header:
      frame_id: "map"
    pose:
      position:
        x: 2.0
        y: 1.0
        z: 0.0
      orientation:
        x: 0.0
        y: 0.0
        z: 0.0
        w: 1.0
  behavior_tree: ""    # leave empty for default
```

**Important:** Before sending an absolute goal, subscribe to `/pose` (type: `geometry_msgs/msg/PoseWithCovarianceStamped`) to verify the robot is localized, and confirm the target coordinates make sense within the map context. If the action times out, the target may be blocked or invalid.

---

## 4. Controlling the Arm

### 4.1 Arm Joint Names and Limits

The arm has 5 joints in the **`hand`** MoveIt planning group:

| Joint Name | Description | Chain Order |
|-----------|-------------|-------------|
| `roarm_base_link_to_link1` | Base rotation (yaw) | 1st |
| `link1_to_link2` | Shoulder pitch | 2nd |
| `link2_to_link3` | Elbow pitch | 3rd |
| `link3_to_link4` | Wrist pitch | 4th |
| `link4_to_link5` | Wrist roll | 5th |

### 4.2 Named Arm Poses

| Pose Name | Joint Values (in order) | Description |
|-----------|------------------------|-------------|
| **home** | `[0, 0, 1.5708, 0, 0]` | Arm folded up vertically |
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
*Note: You must provide a valid orientation. For a downward-facing gripper, use roughly `Yaw: 2.11` or look at the current orientation from Section 13.*

**Example Tool Input (`call_service`):**
```json
{
  "service_name": "/compute_ik",
  "service_type": "moveit_msgs/srv/GetPositionIK",
  "request": {
    "ik_request": {
      "group_name": "hand",
      "pose_stamped": {
        "header": {"frame_id": "base_link"},
        "pose": {
          "position": {"x": 0.2, "y": 0.0, "z": 0.15},
          "orientation": {"x": 0.0, "y": 0.0, "z": 0.0, "w": 1.0}
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

### 6.5 Robot Pose (SLAM)
```
Topic: /pose
Type: geometry_msgs/msg/PoseWithCovarianceStamped
```
Robot's estimated pose in the map frame (from SLAM).

---

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

---

## 8. Available Actions — Complete Reference

| Action | Type | Purpose |
|--------|------|---------|
| `/drive_on_heading` | `nav2_msgs/action/DriveOnHeading` | Drive straight forward |
| `/backup` | `nav2_msgs/action/BackUp` | Drive straight backward |
| `/spin` | `nav2_msgs/action/Spin` | Rotate in place |
| `/navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | Autonomous navigation to a map pose |
| `/navigate_through_poses` | `nav2_msgs/action/NavigateThroughPoses` | Navigate through multiple waypoints |
| `/follow_waypoints` | `nav2_msgs/action/FollowWaypoints` | Follow a sequence of waypoints |
| `/follow_path` | `nav2_msgs/action/FollowPath` | Follow a pre-computed path |
| `/compute_path_to_pose` | `nav2_msgs/action/ComputePathToPose` | Compute a path (no execution) |
| `/assisted_teleop` | `nav2_msgs/action/AssistedTeleop` | Collision-aware teleoperation |
| `/wait` | `nav2_msgs/action/Wait` | Wait for a specified duration |
| `/hand_controller/follow_joint_trajectory` | `control_msgs/action/FollowJointTrajectory` | Move the arm |
| `/gripper_controller/gripper_cmd` | `control_msgs/action/GripperCommand` | Open/close the gripper |
| `/move_action` | `moveit_msgs/action/MoveGroup` | MoveIt motion planning (advanced) |
| `/execute_trajectory` | `moveit_msgs/action/ExecuteTrajectory` | Execute a MoveIt-planned trajectory |

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

---

## 11. Speed Guidelines

| Motion Type | Recommended Speed | Max Speed |
|-------------|------------------|-----------|
| Forward driving | 0.2 m/s | 0.3 m/s |
| Backward driving | 0.15 m/s | 0.2 m/s |
| Arm movement | 3 seconds per motion | 1 second minimum |
| Time allowance (all Nav2 behaviors) | 30 seconds | 60 seconds |

---

## 16. High-Level Tools Reference (Recommended)

| MCP Tool Name | Arguments | ROS Equivalent |
|---------------|-----------|----------------|
| `move_arm_xyz` | `x, y, z` | `/compute_ik` + `/hand_controller/...` |
| `drive_straight` | `distance, speed` | `/drive_on_heading` or `/backup` |
| `turn` | `angle_degrees` | `/spin` |
| `stop_robot` | (none) | Goal Cancellation |
| `open_gripper` | (none) | `/gripper_controller/...` (pos: 0.0) |
| `close_gripper` | (none) | `/gripper_controller/...` (pos: -1.545) |

---

## 12. Error Handling

- If an action returns a non-zero `error_code`, report the error to the user
- If `COLLISION_AHEAD` is returned, the robot detected an obstacle — try an alternate path
- If `TIMEOUT` is returned, increase `time_allowance` or reduce the target distance
- If arm trajectory returns `GOAL_TOLERANCE_VIOLATED`, the arm could not reach the target — try a closer position
- Always verify action completion by checking the result, do not assume success
- Be absolutely sure that the command you promise to send is actually sent! 


### 13. Retrieving Poses and Transforms

Calculating the position of a link (like `link5`) relative to another (like `base_link`) **MUST** be done by resolving the kinematic chain. Because the `/tf` topic is fragmented and the `/rosapi/get_transform` service may be unavailable, follow these protocols in order of priority.

#### 13.1 The "Terminal Echo" Protocol (High Reliability)
If a direct service call fails or is missing, use the **`terminal`** tool. This is the most effective way to resolve a transform because it handles the TF buffer internally.

**Crucial Path Instruction**: When using the `terminal` tool, you **must** specify the working directory, otherwise it will fail with a `cd` error.

* **Tool:** `terminal`
* **Command:** `timeout 5s ros2 run tf2_ros tf2_echo base_link link5`
* **CWD / CD Parameter:** `/home/alexander/simplebot3/ros_ws`

**Example Tool Input:**
```json
{
  "command": "timeout 5s ros2 run tf2_ros tf2_echo base_link link5",
  "cwd": "/home/alexander/simplebot3/ros_ws",
  "cd": "/home/alexander/simplebot3/ros_ws"
}
```
*(Include both `cwd` and `cd` just in case your specific terminal tool variant uses the other name).*
*Wait for the terminal output, which will provide `At time... Translation: [x, y, z]`.*

#### 13.2 The Service Call Protocol (Preferred if Active)
Use the `call_service` tool only if the `/rosapi/get_transform` service is active in the environment.

* **Service Name:** `/rosapi/get_transform`
* **Service Type:** `rosapi_msgs/srv/GetTransform`
* **Syntax (STRICT):** The `request` argument **MUST** be a valid JSON dictionary, not a string.

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

### 14. Execution Integrity & Tool Usage
### 14.1 Actual vs. Described Action (ANTI-HALLUCINATION PROTOCOL)

You must maintain a strict 1:1 relationship between your words and your tool calls.

**🚨 CRITICAL: NARRATION IS NOT EXECUTION!**
Saying "I will now call the tool" or "I am calling `call_service`" in plain text **DOES NOTHING**. The robot will just sit there.
To actually perform an action, you **MUST** emit the formal native tool-calling structure (e.g., the specific tool invocation API or JSON format your system uses). 

1. **Do not write** "I am moving the arm..." unless your *very next output* is the formal tool invocation.
2. **Never claim** an action was successful until you receive the actual JSON response from the tool execution.
3. If the tool call fails or parses incorrectly (e.g., getting string/JSON errors), do not pretend it worked. Fix your JSON syntax and use the tool again formally.

### 14.2 Multi-Step Verification

When performing a task (e.g., "Pick up the block"):

1. Call tool to move arm.
2. Wait for tool output.
3. Call tool to close gripper.
4. Wait for tool output.
5. Report final status.

### 15. Speed and Safety Guidelines

| Motion Type | Recommended Speed | Max Speed |
|-------------|------------------|-----------|
| Forward driving | 0.2 m/s | 0.3 m/s |
| Backward driving | 0.15 m/s | 0.2 m/s |
| Arm movement | 3 seconds per motion | 1 second minimum |
| Time allowance (all Nav2 behaviors) | 30 seconds | 60 seconds |