cmake_minimum_required(VERSION 2.8.3)
project(robot_description)

find_package(catkin REQUIRED)
catkin_package()

install(DIRECTORY urdf meshes launch config
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}
)
