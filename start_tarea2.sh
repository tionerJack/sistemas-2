#!/bin/bash
# start_tarea2.sh - Inicia todo el stack Tarea 2 (AMCL Localization)
# Ejecutar: bash start_tarea2.sh
# Requiere: contenedor ros_noetic_sim corriendo

set -e

echo "============================================"
echo "  Tarea 2 - AMCL Localization Stack"
echo "============================================"

echo ""
echo "[1/8] Limpiando nodos gz previos..."
sudo docker exec ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && rosnode kill /gazebo 2>/dev/null; rosnode kill /gazebo_server 2>/dev/null; pkill -f "gzserver" 2>/dev/null; pkill -f "gzclient" 2>/dev/null' || true
sleep 2

echo "[2/8] Iniciando gzserver (__name:=gazebo_server)..."
sudo docker exec -d ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && source /ros_ws/devel/setup.bash && export GAZEBO_MODEL_PATH=/ros_ws/src/robot_gazebo/models && export GAZEBO_RESOURCE_PATH=/ros_ws/src/robot_gazebo && rosrun gazebo_ros gzserver /ros_ws/src/robot_gazebo/launch/warehouse.world --verbose __name:=gazebo_server'
echo "   Esperando 10s a que inicialice..."
sleep 10

echo "[3/8] Verificando /clock..."
sudo docker exec ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && rostopic echo /clock -n1 2>/dev/null | head -3' || { echo "ERROR: /clock no disponible"; exit 1; }
echo "   ✅ /clock OK"

echo "[4/8] Spawneando robot + laser..."
sudo docker exec ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && source /ros_ws/devel/setup.bash && export GAZEBO_MODEL_PATH=/ros_ws/src/robot_gazebo/models && rosrun gazebo_ros spawn_model -file /ros_ws/src/robot_gazebo/models/robot_nolaser.sdf -sdf -model robot -x 0.0 -y 0.0 -z 0.5 -Y 0.0'
sleep 1
sudo docker exec ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && source /ros_ws/devel/setup.bash && export GAZEBO_MODEL_PATH=/ros_ws/src/robot_gazebo/models && rosrun gazebo_ros spawn_model -file /ros_ws/src/robot_gazebo/models/laser_model.sdf -sdf -model laser -x 0.275 -y 0.0 -z 0.30 -Y 0.0'
echo "   ✅ Robot + laser spawneados"

echo "[5/8] Iniciando map_server..."
sudo docker exec ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && rosnode list | grep map_server' 2>/dev/null || \
sudo docker exec -d ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && rosrun map_server map_server /ros_ws/maps/warehouse_map.yaml'
sleep 2
echo "   ✅ map_server OK"

echo "[6/8] Iniciando AMCL..."
sudo docker exec ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && rosnode list | grep amcl' 2>/dev/null || \
sudo docker exec -d ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && rosrun amcl amcl _scan:=scan _base_frame_id:=base_link _odom_frame_id:=odom _global_frame_id:=map _initial_pose_x:=0.0 _initial_pose_y:=0.0 _initial_pose_a:=0.0 _laser_model_type:=likelihood_field _laser_likelihood_max_dist:=2.0 _laser_max_range:=10.0'
sleep 2
echo "   ✅ AMCL OK"

echo "[7/8] Cargando robot_description + robot_state_publisher..."
sudo docker exec ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && rosparam set robot_description "$(rosrun xacro xacro /ros_ws/src/robot_description/urdf/robot.xacro)"'
sudo docker exec -d ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && rosrun robot_state_publisher robot_state_publisher __name:=rsp'
sleep 1
echo "   ✅ robot_description + RSP OK"

echo "[8/8] Lanzando GUIs (software rendering)..."
sudo docker exec -d ros_noetic_sim bash -c 'export DISPLAY=:0 && export LIBGL_ALWAYS_SOFTWARE=1 && export GALLIUM_DRIVER=llvmpipe && export OGRE_RTT_MODE=Copy && source /opt/ros/noetic/setup.bash && source /ros_ws/devel/setup.bash && rosrun gazebo_ros gzclient __name:=gzclient'
sleep 3
sudo docker exec -d ros_noetic_sim bash -c 'export DISPLAY=:0 && export LIBGL_ALWAYS_SOFTWARE=1 && export GALLIUM_DRIVER=llvmpipe && export OGRE_RTT_MODE=Copy && source /opt/ros/noetic/setup.bash && source /ros_ws/devel/setup.bash && rosrun rviz rviz -d /ros_ws/src/robot_gazebo/config/amcl.rviz __name:=rviz'

echo ""
echo "============================================"
echo "  ✅ STACK TAREA 2 INICIADO"
echo "============================================"
echo ""
echo "Ventanas esperadas:"
echo "  - Gazebo (warehouse + robot + laser)"
echo "  - RViz (mapa + laser + partículas AMCL)"
echo ""
echo "Para MOVER el robot (programado):"
echo '  sudo docker exec ros_noetic_sim bash -c '\''source /opt/ros/noetic/setup.bash && rostopic pub -1 /cmd_vel geometry_msgs/Twist "{linear: {x: 0.3, y: 0.0, z: 0.0}, angular: {z: 0.0}}"\'
echo ""
echo "Para TELEOP interactivo (OTRA terminal):"
echo "  sudo docker exec -it ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && rosrun teleop_twist_keyboard teleop_twist_keyboard.py'"
echo ""
echo "Verificar topics:"
echo "  sudo docker exec ros_noetic_sim bash -c 'source /opt/ros/noetic/setup.bash && rostopic list'"
