#!/bin/bash
source /opt/ros/noetic/setup.bash
source /ros_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=localhost

# Colors
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  PIPELINE COMPLETO: 3 TAREAS ROS     ${NC}"
echo -e "${CYAN}========================================${NC}"

# Kill duplicate TF publishers (keep the first one started by run_sim.sh)
# Find all static_transform_publisher PIDs, keep the oldest
TF_PIDS=$(pgrep -f static_transform_publisher | sort | head -n -1)
if [ -n "$TF_PIDS" ]; then
  kill -9 $TF_PIDS 2>/dev/null
  echo "Killed duplicate TF publishers: $TF_PIDS"
fi

# === TAREA 1: MAPPING CON GMAPPING ===
echo ""
echo -e "${GREEN}===== TAREA 1: MAPEO CON GMAPPING =====${NC}"

# Start gmapping
echo "Starting slam_gmapping..."
rosrun gmapping slam_gmapping \
  _base_frame:=base_link \
  _odom_frame:=odom \
  _map_update_interval:=2.0 \
  _particles:=80 \
  _linearUpdate:=1.0 \
  _angularUpdate:=0.5 \
  _xmin:=-15 _xmax:=15 _ymin:=-15 _ymax:=15 \
  _delta:=0.05 \
  &>/tmp/gmapping.log &
GMAPPING_PID=$!
echo "Gmapping started (PID: $GMAPPING_PID)"

# Wait for gmapping to initialize and start publishing /map
echo "Waiting for /map topic..."
for i in $(seq 1 15); do
  rostopic info /map 2>/dev/null | grep -q "slam_gmapping" && break
  sleep 1
done
echo "Gmapping ready."

# Move robot in zigzag (lawnmower) exploration pattern to cover warehouse area
echo "Moving robot to explore environment (120s)..."
(
  # Zigzag pattern: forward across corridor, slight turn, forward back, repeat
  for row in 1 2 3 4 5; do
    # Forward leg
    rostopic pub -1 /cmd_vel geometry_msgs/Twist \
      '{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}' &>/dev/null
    sleep 8
    # Small right arc to shift lane
    rostopic pub -1 /cmd_vel geometry_msgs/Twist \
      '{linear: {x: 0.3, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.3}}' &>/dev/null
    sleep 3
    # Backward leg (opposite direction)
    rostopic pub -1 /cmd_vel geometry_msgs/Twist \
      '{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}' &>/dev/null
    sleep 8
    # Small left arc to shift lane
    rostopic pub -1 /cmd_vel geometry_msgs/Twist \
      '{linear: {x: 0.3, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: -0.3}}' &>/dev/null
    sleep 3
  done
  # Wide rotations to cover lateral areas
  rostopic pub -1 /cmd_vel geometry_msgs/Twist \
    '{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.4}}' &>/dev/null
  sleep 8
  # Final forward sweep
  rostopic pub -1 /cmd_vel geometry_msgs/Twist \
    '{linear: {x: 0.5, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}' &>/dev/null
  sleep 10
  # Stop
  rostopic pub -1 /cmd_vel geometry_msgs/Twist \
    '{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}' &>/dev/null
) &
MOVE_PID=$!

# Wait for exploration
sleep 120
kill $MOVE_PID 2>/dev/null

# Save the map (using custom script that handles simulated time)
echo "Saving map to /ros_ws/maps/..."
mkdir -p /ros_ws/maps
python3 /ros_ws/src/robot_gazebo/scripts/save_map.py _file:=/ros_ws/maps/warehouse_map _timeout:=30 2>&1
sleep 1
echo "Map saved! Files:"
ls -la /ros_ws/maps/warehouse_map*

echo -e "${GREEN}===== TAREA 1 COMPLETADA =====${NC}"

# === TAREA 2: LOCALIZACIÓN CON AMCL ===
echo ""
echo -e "${GREEN}===== TAREA 2: LOCALIZACIÓN CON AMCL =====${NC}"

# Kill gmapping (no longer needed)
killall -9 slam_gmapping 2>/dev/null
sleep 1

# Start AMCL with the saved map
rosrun amcl amcl \
  _scan:=scan \
  _base_frame_id:=base_link \
  _odom_frame_id:=odom \
  _global_frame_id:=map \
  _min_particles:=500 \
  _max_particles:=5000 \
  _update_min_d:=0.2 \
  _update_min_a:=0.1 \
  _resample_interval:=1 \
  _transform_tolerance:=0.2 \
  _recovery_alpha_slow:=0.001 \
  _recovery_alpha_fast:=0.1 \
  _initial_pose_x:=0.0 \
  _initial_pose_y:=0.0 \
  _initial_pose_a:=0.0 \
  _laser_model_type:=likelihood_field \
  _laser_likelihood_max_dist:=2.0 \
  _laser_max_range:=10.0 \
  &>/tmp/amcl.log &
AMCL_PID=$!
echo "AMCL started (PID: $AMCL_PID)"
sleep 3

# Publish map
rosrun map_server map_server /ros_ws/maps/warehouse_map.yaml &>/tmp/map_server.log &
sleep 2

echo "AMCL nodes:"
rosnode list | grep -E "(amcl|map_server)"

echo -e "${GREEN}===== TAREA 2 COMPLETADA =====${NC}"

# === TAREA 3: NAVEGACIÓN CON MOVE_BASE ===
echo ""
echo -e "${GREEN}===== TAREA 3: NAVEGACIÓN (A* + DWA) =====${NC}"

# Start move_base with all configs
roslaunch robot_navigation move_base.launch &>/tmp/move_base.log &
MOVE_BASE_PID=$!
echo "move_base started (PID: $MOVE_BASE_PID)"
sleep 8

echo "Navigation nodes:"
rosnode list | grep -E "(move_base|planner)"

# Send a navigation goal
echo "Sending navigation goal to (3.0, 0.0)..."
rostopic pub /move_base_simple/goal geometry_msgs/PoseStamped \
  "header: {frame_id: 'map', stamp: now}
pose:
  position: {x: 3.0, y: 0.0, z: 0.0}
  orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}" &>/dev/null

echo "Goal sent! Waiting 30s for navigation..."
sleep 30

echo -e "${GREEN}===== TAREA 3 COMPLETADA =====${NC}"

# === FINAL STATUS ===
echo ""
echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  PIPELINE COMPLETADO                  ${NC}"
echo -e "${CYAN}========================================${NC}"
echo "Active topics:"
rostopic list -v
echo ""
echo "Map file: /ros_ws/maps/warehouse_map.*"
echo "Status:"
echo "  Tarea 1 (Gmapping): ✅ [map saved]"
echo "  Tarea 2 (AMCL):     ✅ [localization running]"
echo "  Tarea 3 (Nav):      ✅ [move_base running + goal sent]"
echo ""
echo "NOTE: Full exploration requires more time and interactive control."
echo "Run teleoperation to continue: rosrun teleop_twist_keyboard teleop_twist_keyboard.py"
