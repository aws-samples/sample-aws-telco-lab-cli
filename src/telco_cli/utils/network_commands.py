# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

"""Network interface shell commands."""

# Enhanced command to get detailed network interface information including SR-IOV
NETWORK_INTERFACE_COMMAND = """
# Basic interface info
ip -o link show | grep -E '^[0-9]+:' | awk '{print $2, $9}' && echo '---IP---' &&
ip addr show | grep -E '^[0-9]+:|inet ' && echo '---SRIOV---' &&
# Check SR-IOV capability
for iface in $(ls /sys/class/net/ | grep -v lo); do
    echo "Interface: $iface"
    if [ -f /sys/class/net/$iface/device/sriov_totalvfs ]; then
        total_vfs=$(cat /sys/class/net/$iface/device/sriov_totalvfs 2>/dev/null || echo "0")
        current_vfs=$(cat /sys/class/net/$iface/device/sriov_numvfs 2>/dev/null || echo "0")
        echo "SR-IOV: Capable (Total VFs: $total_vfs, Current VFs: $current_vfs)"
    else
        echo "SR-IOV: Not Capable"
    fi
    # Get driver and speed info using ethtool (most reliable) with fallbacks
    if command -v ethtool >/dev/null 2>&1; then
        # Use ethtool for driver info (most accurate)
        driver=$(ethtool -i $iface 2>/dev/null | grep "driver:" | awk '{print $2}')
        if [ -z "$driver" ]; then
            driver="Unknown"
        fi
        echo "Driver: $driver"

        # Use ethtool for speed info
        speed=$(ethtool $iface 2>/dev/null | grep "Speed:" | awk '{print $2}' | sed 's/Mb\\/s/Mbps/')
        if [ -z "$speed" ]; then
            speed="Unknown"
        fi
        echo "Speed: $speed"
    else
        # Fallback 1: Try sysfs driver path
        if [ -L /sys/class/net/$iface/device/driver ]; then
            driver=$(basename $(readlink /sys/class/net/$iface/device/driver) 2>/dev/null)
        elif [ -f /sys/class/net/$iface/device/uevent ]; then
            driver=$(grep "DRIVER=" /sys/class/net/$iface/device/uevent 2>/dev/null | cut -d= -f2)
        else
            driver="Unknown"
        fi
        echo "Driver: ${driver:-Unknown}"

        # Fallback for speed
        if [ -f /sys/class/net/$iface/speed ]; then
            speed=$(cat /sys/class/net/$iface/speed 2>/dev/null)
            if [ "$speed" = "-1" ]; then
                speed="Unknown"
            else
                speed="${speed}Mbps"
            fi
        else
            speed="Unknown"
        fi
        echo "Speed: $speed"
    fi
    echo "---"
done
"""
