#!/bin/bash
# ============================================
# RECORDING SCRIPT: TAREA 1 - MAPEO CON GMAPPING
# ============================================
# Uso: bash /ros_ws/record_tarea1.sh
# Graba video del mapeo explorando el almacén
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
echo -e "${CYAN}  TAREA 1: MAPEO CON GMAPPING         ${NC}"
echo -e "${CYAN}========================================${NC}"

# Kill stale
killall -9 gzserver roscore python3 2>/dev/null
sleep 2

# Start roscore
echo "[1/5] Starting roscore..."
roscore &>/tmp/roscore.log &
sleep 3

# Enable simulated time
rosparam set use_sim_time true

# Start Gazebo
echo "[2/5] Starting Gazebo..."
rosrun gazebo_ros gzserver /ros_ws/src/robot_gazebo/launch/warehouse.world --verbose &>/tmp/gzserver.log &
sleep 12

# Spawn robot + laser
echo "[3/5] Spawning robot and laser..."
rosrun gazebo_ros spawn_model -sdf -file /ros_ws/src/robot_gazebo/models/robot_nolaser.sdf -model differential_robot -x 0 -y 0 -z 0.1
sleep 2
rosrun gazebo_ros spawn_model -sdf -file /ros_ws/src/robot_gazebo/models/laser_model.sdf -model laser_sensor -x 0 -y 0 -z 0.1
sleep 2

# Static TF
rosrun tf static_transform_publisher 0.15 0 0.08 0 0 0 base_link laser_frame 50 &>/tmp/tf_laser.log &

# Start Gmapping
echo "[4/5] Starting Gmapping SLAM..."
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
sleep 3

echo -e "${GREEN}[5/5] TAREA 1 LISTA PARA GRABAR${NC}"
echo "========================================"
echo -e "  ${YELLOW}Abre RViz para ver el mapa:${NC}"
echo '    rviz -d /ros_ws/src/robot_description/config/robot.rviz'
echo ""
echo -e "  ${YELLOW}Abre Gazebo GUI para ver el 3D:${NC}"
echo "    gzclient"
echo ""
echo -e "  ${YELLOW}Teleoperación (en otra terminal):${NC}"
echo '    rostopic pub /cmd_vel geometry_msgs/Twist "{linear: {x: 0.4}}"'
echo '    rostopic pub /cmd_vel geometry_msgs/Twist "{angular: {z: 0.5}}"'
echo '    rostopic pub /cmd_vel geometry_msgs/Twist "{linear: {x: 0.0}}"'
echo ""
echo -e "  ${YELLOW}Tópicos activos:${NC}"
rostopic list
echo ""
echo -e "  ${YELLOW}Para guardar el mapa al terminar:${NC}"
echo '    python3 /ros_ws/src/robot_gazebo/scripts/save_map.py _file:=/ros_ws/maps/warehouse_map _timeout:=30'
echo "========================================"
