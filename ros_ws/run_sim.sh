#!/bin/bash
source /opt/ros/noetic/setup.bash
source /ros_ws/devel/setup.bash
export ROS_MASTER_URI=http://localhost:11311
export ROS_HOSTNAME=localhost

echo "========================================"
echo "  SIMULACIÓN COMPLETA: NAVEGACIÓN ROS  "
echo "========================================"

# === 1. KILL STALE PROCESSES ===
killall -9 gzserver roscore python3 2>/dev/null
sleep 2

# === 2. START ROSCORE ===
echo "[1/7] Starting roscore..."
roscore &>/tmp/roscore.log &
sleep 3

# === 2b. ENABLE SIMULATED TIME ===
echo "[1b/7] Enabling simulated time..."
rosparam set use_sim_time true
echo "use_sim_time = true"

# === 3. START GAZEBO ===
echo "[2/7] Starting Gazebo with warehouse world..."
rosrun gazebo_ros gzserver /ros_ws/src/robot_gazebo/launch/warehouse.world --verbose &>/tmp/gzserver.log &
sleep 12

# === 4. SPAWN ROBOT (diff_drive only) ===
echo "[3/7] Spawning robot (diff_drive)..."
rosrun gazebo_ros spawn_model -sdf -file /ros_ws/src/robot_gazebo/models/robot_nolaser.sdf -model differential_robot -x 0 -y 0 -z 0.1
sleep 2

# === 5. SPAWN LASER (separate model) ===
echo "[4/7] Spawning laser sensor..."
rosrun gazebo_ros spawn_model -sdf -file /ros_ws/src/robot_gazebo/models/laser_model.sdf -model laser_sensor -x 0 -y 0 -z 0.1
sleep 2

# === 6. PUBLISH STATIC TF base_link→laser_frame ===
echo "[5/7] Publishing static TF base_link→laser_frame..."
rosrun tf static_transform_publisher 0.15 0 0.08 0 0 0 base_link laser_frame 50 &>/tmp/tf_laser.log &
sleep 1

echo "=== ACTIVE TOPICS ==="
rostopic list
echo ""
echo "=== PARAMETERS ==="
rosparam get use_sim_time

echo ""
echo "========================================"
echo "  SIMULACIÓN LISTA                     "
echo "========================================"
echo "  /odom    - Odometría (diff_drive)    "
echo "  /scan    - Láser 270° 20Hz           "
echo "  /tf      - Transformadas             "
echo "  /cmd_vel - Comando de velocidad      "
echo "========================================"
