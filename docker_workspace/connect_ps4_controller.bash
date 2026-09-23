#!/usr/bin/env bash

MAC="8C:41:F2:8B:60:4A"

echo "[INFO] Resetting and reconnecting to $MAC..."

# Use a here-doc to feed commands to bluetoothctl
bluetoothctl <<EOF
remove $MAC
scan on
pair $MAC
trust $MAC
connect $MAC
scan off
EOF

# Now check connection status
CONNECTED=$(bluetoothctl info "$MAC" | grep "Connected: yes")

if [ -n "$CONNECTED" ]; then
    echo "[SUCCESS] Controller $MAC connected successfully!"
    exit 0
else
    echo "[ERROR] Failed to connect to controller $MAC."
    exit 1
fi
