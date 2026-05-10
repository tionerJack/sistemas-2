#!/bin/bash
source /opt/ros/noetic/setup.bash
source /ros_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=localhost

echo "=== 1. roscore ==="
roscore &>/tmp/roscore.log &
sleep 3

echo "=== 2. gzserver (ROS plugin) ==="
rosrun gazebo_ros gzserver /ros_ws/src/robot_gazebo/launch/warehouse.world --verbose &>/tmp/gzserver.log &
sleep 12

echo "=== 3. Topics ==="
rostopic list -v
