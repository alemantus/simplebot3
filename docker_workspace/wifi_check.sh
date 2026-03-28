#!/bin/bash

# Load environment variables from a secure .env file
ENV_FILE="/etc/wifi_hotspot.env"

if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | xargs)
else
    echo "Environment file not found! Exiting..."
    exit 1
fi

# Set variables
SSID="m6_network"
WIFI_INTERFACE="wlo1"

# Delay execution for 10 seconds
sleep 1

# Function to check if connected to a Wi-Fi network
check_wifi() {
    nmcli -t -f ACTIVE,DEVICE,TYPE con show --active | grep -E "wireless" | grep "yes"
    #nmcli -t -f ACTIVE,DEVICE,TYPE con show --active | grep -E "wifi" | grep "yes"
}

# If not connected to Wi-Fi, start hotspot
if ! check_wifi; then
    echo "$(date) - No Wi-Fi connection detected. Starting hotspot..."
    nmcli dev wifi hotspot ssid "$SSID" password "$HOTSPOT_PASSWORD"
else
    echo "$(date) - Connected to Wi-Fi. No action needed."
fi
