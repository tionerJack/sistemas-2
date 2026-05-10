#!/bin/bash
set -e

# Add ROS setup to .bashrc for interactive shells
echo "source /opt/ros/noetic/setup.bash" >> ~/.bashrc
echo "source /ros_ws/devel/setup.bash" >> ~/.bashrc
echo "export ROS_MASTER_URI=http://localhost:11311" >> ~/.bashrc
echo "export ROS_HOSTNAME=localhost" >> ~/.bashrc

# Build workspace
cd /ros_ws
catkin_make 2>/dev/null || true

# Source for this session
source /opt/ros/noetic/setup.bash
source /ros_ws/devel/setup.bash

exec "$@"
