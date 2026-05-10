#!/bin/bash
cd /ros_ws
source /opt/ros/noetic/setup.bash
source /ros_ws/devel/setup.bash
rosrun xacro xacro /ros_ws/src/robot_description/urdf/robot.xacro > /tmp/robot.urdf 2>&1
echo "EXIT: $?"
head -60 /tmp/robot.urdf
echo "..."
echo "--- check_urdf ---"
check_urdf /tmp/robot.urdf 2>&1 || true
