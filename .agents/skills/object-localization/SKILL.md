# Object Localization Skill

This skill allows the AI to precisely locate objects in 3D space using the segmentation-refined detections.

## 🛠 Tool Usage (High-Level MCP Tool)

To find the precise 3D position of an object, use the **`get_object_position`** tool. This is the primary and most reliable method.

### Example Tool Invocation

```json
{
  "class_name": "green cube"
}
```

### Expected Output

```json
{
  "success": true,
  "class_name": "green cube",
  "position": {
    "x": 0.5241,
    "y": -0.0123,
    "z": 0.4502
  },
  "frame_id": "femto_bolt_depth_optical_frame",
  "score": 0.89
}
```

## 🔄 Alternative Usage (Raw ROS)

If the high-level tool fails, use `subscribe_once` on the raw topic:

- **Topic**: `/yolo/detections_3d`
- **Type**: `yolo_msgs/msg/DetectionArray`

Filter the `detections` array for the target `class_name` and extract `bbox3d.center.position`.
