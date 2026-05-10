FROM osrf/ros:noetic-desktop-full

# Instalar dependencias ROS
RUN apt-get update && apt-get install -y \
    ros-noetic-gmapping \
    ros-noetic-amcl \
    ros-noetic-move-base \
    ros-noetic-dwa-local-planner \
    ros-noetic-map-server \
    ros-noetic-teleop-twist-keyboard \
    ros-noetic-robot-state-publisher \
    ros-noetic-joint-state-publisher-gui \
    ros-noetic-xacro \
    ros-noetic-gazebo-ros-pkgs \
    ros-noetic-gazebo-ros-control \
    ros-noetic-ros-control \
    ros-noetic-ros-controllers \
    ros-noetic-navigation \
    ros-noetic-slam-gmapping \
    && rm -rf /var/lib/apt/lists/*

# Crear workspace
RUN mkdir -p /ros_ws/src
WORKDIR /ros_ws

# Script de entrada
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
CMD ["bash"]
