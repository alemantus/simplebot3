#!/bin/bash
# patch_yolo_shebangs.sh
# Run this after every `colcon build` to point yolo_ros node scripts at venv_yolo.
# colcon generates these wrapper scripts using whatever Python is active at build time,
# overwriting the shebang — so this patch must be re-applied after each build.

set -e

YOLO_PYTHON="/home/alexander/venv_yolo/bin/python3"
INSTALL_DIR="/home/alexander/simplebot3/ros_ws/install/yolo_ros/lib/yolo_ros"

NODES=(yolo_node debug_node tracking_node detect_3d_node)

echo "Patching yolo_ros node shebangs -> $YOLO_PYTHON"
for node in "${NODES[@]}"; do
    target="$INSTALL_DIR/$node"
    if [ -f "$target" ]; then
        sed -i "1s|.*|#!${YOLO_PYTHON}|" "$target"
        echo "  Patched: $target"
    else
        echo "  Skipped (not found): $target"
    fi
done
echo "Done."
