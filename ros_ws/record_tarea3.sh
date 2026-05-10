#!/bin/bash
# ============================================
# RECORDING SCRIPT: TAREA 3 - NAVEGACIÓN CON MOVE_BASE
# ============================================
# Uso: bash /ros_ws/record_tarea3.sh
# Graba video del robot navegando autónomamente
# ============================================

source /opt/ros/noetic/setup.bash
source /ros_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=localhost

GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${CYAN}========================================${NC}"
echo -e "${CYAN}  TAREA 3: NAVEGACIÓN (A* + DWA)       ${NC}"
echo -e "${CYAN}========================================${NC}"

# Kill stale
killall -9 gzserver roscore python3 2>/dev/null
sleep 2

# Start roscore
echo "[1/6] Starting roscore..."
roscore &>/tmp/roscore.log &
sleep 3

# Enable simulated time
rosparam set use_sim_time true

# Start Gazebo
echo "[2/6] Starting Gazebo..."
rosrun gazebo_ros gzserver /ros_ws/src/robot_gazebo/launch/warehouse.world --verbose &>/tmp/gzserver.log &
sleep 12

# Spawn robot + laser
echo "[3/6] Spawning robot and laser..."
rosrun gazebo_ros spawn_model -sdf -file /ros_ws/src/robot_gazebo/models/robot_nolaser.sdf -model differential_robot -x 0 -y 0 -z 0.1
sleep 2
rosrun gazebo_ros spawn_model -sdf -file /ros_ws/src/robot_gazebo/models/laser_model.sdf -model laser_sensor -x 0 -y 0 -z 0.1
sleep 2

# Static TF
rosrun tf static_transform_publisher 0.15 0 0.08 0 0 0 base_link laser_frame 50 &>/tmp/tf_laser.log &

# Map server + AMCL
echo "[4/6] Loading map + starting AMCL..."
rosrun map_server map_server /ros_ws/maps/warehouse_map.yaml &>/tmp/map_server.log &
sleep 2
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
sleep 3

# Start move_base with A* global + DWA local
echo "[5/6] Starting move_base..."
roslaunch robot_navigation move_base.launch &>/tmp/move_base.log &
sleep 8

echo -e "${GREEN}[6/6] TAREA 3 LISTA PARA GRABAR${NC}"
echo "========================================"
echo -e "  ${YELLOW}Abre RViz:${NC}"
echo '    rviz -d /ros_ws/src/robot_description/config/robot.rviz'
echo ""
echo -e "  ${YELLOW}Abre Gazebo GUI:${NC}"
echo "    gzclient"
echo ""
echo -e "  ${YELLOW}Envía una meta de navegación:${NC}"
echo '    rostopic pub /move_base_simple/goal geometry_msgs/PoseStamped \
  "header: {frame_id: '"'"'map'"'"', stamp: now}
pose:
  position: {x: 3.0, y: 2.0, z: 0.0}
  orientation: {x: 0.0, y: 0.0, z: 0.0, w: 1.0}"'
echo ""
echo -e "  ${YELLOW}Tópicos activos:${NC}"
rostopic list
echo "========================================"
