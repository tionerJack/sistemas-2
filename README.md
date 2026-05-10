# Simulación de Navegación Autónoma — ROS Noetic + Gazebo

Pipeline completo de 3 tareas: **Mapeo (Gmapping)** → **Localización (AMCL)** → **Navegación (A\* + DWA)**.

## Requisitos

- Docker Engine ≥ 24.0
- Grupo `docker` configurado para el usuario: `sudo usermod -aG docker $USER`

## 1. Construir imagen

```bash
cd docker
docker compose build
```

## 2. Iniciar contenedor

```bash
docker compose up -d
```

## 3. Ejecutar simulación completa (automático)

```bash
# Iniciar Gazebo + robot + láser
sg docker -c "docker exec ros_noetic_sim bash /ros_ws/run_sim.sh"

# Ejecutar pipeline 3 tareas
sg docker -c "docker exec ros_noetic_sim bash /ros_ws/run_all.sh"
```

### Qué hace `run_all.sh`

| Paso | Acción                                               |
| ---- | ---------------------------------------------------- |
| 1    | Inicia `slam_gmapping` con partículas=80, delta=0.05 |
| 2    | Mueve el robot en patrón de exploración (60s)        |
| 3    | Guarda el mapa en `/ros_ws/maps/warehouse_map.pgm`   |
| 4    | Detiene gmapping, inicia `map_server` + `amcl`       |
| 5    | Inicia `move_base` con A\* global + DWA local        |
| 6    | Envía goal de navegación a (3.0, 0.0)                |

## 4. Ejecución manual (interactiva)

```bash
docker exec -it ros_noetic_sim bash

# Terminal 1: Gazebo + robot
rosrun gazebo_ros gzserver /ros_ws/src/robot_gazebo/launch/warehouse.world

# Terminal 2: Gmapping
rosrun gmapping slam_gmapping \
  _base_frame:=base_link _odom_frame:=odom _particles:=80

# Terminal 3: Teleoperación (explorar)
rosrun teleop_twist_keyboard teleop_twist_keyboard.py

# Terminal 4: Guardar mapa
python3 /ros_ws/src/robot_gazebo/scripts/save_map.py

# Terminal 5: Localización
rosrun amcl amcl _scan:=scan _base_frame_id:=base_link _odom_frame_id:=odom
rosrun map_server map_server /ros_ws/maps/warehouse_map.yaml

# Terminal 6: Navegación
roslaunch robot_navigation move_base.launch
rostopic pub /move_base_simple/goal geometry_msgs/PoseStamped \
  "header: {frame_id: 'map', stamp: now}
   pose: {position: {x: 3.0, y: 0.0, z: 0.0}, orientation: {w: 1.0}}"
```

## Topología del sistema

```
Gazebo (warehouse.world)
  ├── differential_robot (SDF + diff_drive plugin)
  │     ├── /odom, /tf, /cmd_vel
  │     └── laser_frame (link pasivo)
  └── laser_sensor (SDF estático + ray sensor)
        └── /scan (270°, 20Hz, 0.1–10m)

TF tree: map → odom → base_link → laser_frame (50Hz estático)
```

## Archivos clave

| Archivo                                                                                                          | Propósito                                          |
| ---------------------------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| [`docker/Dockerfile`](docker/Dockerfile)                                                                         | Imagen ROS Noetic + Gazebo                         |
| [`docker/docker-compose.yml`](docker/docker-compose.yml)                                                         | Orquestación del contenedor                        |
| [`ros_ws/run_sim.sh`](ros_ws/run_sim.sh)                                                                         | Inicia Gazebo + robot + láser                      |
| [`ros_ws/run_all.sh`](ros_ws/run_all.sh)                                                                         | Pipeline 3 tareas (automático)                     |
| [`ros_ws/src/robot_gazebo/models/robot_nolaser.sdf`](ros_ws/src/robot_gazebo/models/robot_nolaser.sdf)           | Robot SDF (diff_drive)                             |
| [`ros_ws/src/robot_gazebo/models/laser_model.sdf`](ros_ws/src/robot_gazebo/models/laser_model.sdf)               | Sensor láser SDF                                   |
| [`ros_ws/src/robot_gazebo/scripts/save_map.py`](ros_ws/src/robot_gazebo/scripts/save_map.py)                     | Guarda mapa desde `/map` (soporta tiempo simulado) |
| [`ros_ws/src/robot_slam/launch/gmapping.launch`](ros_ws/src/robot_slam/launch/gmapping.launch)                   | Configuración Gmapping                             |
| [`ros_ws/src/robot_localization/config/amcl_params.yaml`](ros_ws/src/robot_localization/config/amcl_params.yaml) | Parámetros AMCL                                    |
| [`ros_ws/src/robot_navigation/launch/move_base.launch`](ros_ws/src/robot_navigation/launch/move_base.launch)     | Lanzamiento move_base                              |
