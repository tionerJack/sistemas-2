# CONTEXT - Proyecto Integrador: Simulación de Navegación Autónoma

## Estado del Repositorio

- **REQUIREMENTS.md** ✅ — generado con 15 requerimientos, 4 ADRs, diagrama Mermaid, tabla Harvard.
- **ARCHITECTURE.md** ✅ — blueprint técnico completo con parámetros, TF tree, costmaps.
- **TEST_REPORT.md** ✅ — verificación técnica (TST-01) con 2 errores corregidos, 3 advertencias.
- **REVIEW_REPORT.md** ✅ — auditoría final de calidad. **Veredicto: APROBADO** (0 🔴, 0 🟡).
- **trabajo_tenam.tex** ✅ — documento LaTeX completo (1128 líneas, 27 pp.).
- **trabajo_tenam.pdf** ✅ — PDF compilado sin errores.
- **Logo**: `logo.png` — institucional.
- **Plan de estudios**: `Plan de estudios (1).pdf` — fuente académica.

## Entorno Docker ROS Noetic + Gazebo ✅ (NUEVO)

Se implementó el entorno de simulación Dockerizado para ejecución práctica:

| Componente            | Estado       | Archivo                                                  |
| --------------------- | ------------ | -------------------------------------------------------- |
| Docker Engine v29.4.3 | ✅ Instalado | —                                                        |
| Dockerfile            | ✅ Creado    | [`docker/Dockerfile`](docker/Dockerfile)                 |
| docker-compose.yml    | ✅ Creado    | [`docker/docker-compose.yml`](docker/docker-compose.yml) |
| entrypoint.sh         | ✅ Creado    | [`docker/entrypoint.sh`](docker/entrypoint.sh)           |
| Build de imagen       | ✅ Exitoso   | `docker-ros_noetic`                                      |

### Paquetes ROS creados (5 paquetes)

| Paquete              | Propósito                  | Archivos clave                                                                                                                                 |
| -------------------- | -------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- |
| `robot_description`  | URDF del robot diferencial | [`robot.xacro`](ros_ws/src/robot_description/urdf/robot.xacro), [`display.launch`](ros_ws/src/robot_description/launch/display.launch)         |
| `robot_gazebo`       | Configuración Gazebo       | [`spawn_robot.launch`](ros_ws/src/robot_gazebo/launch/spawn_robot.launch), [`warehouse.world`](ros_ws/src/robot_gazebo/launch/warehouse.world) |
| `robot_slam`         | Tarea 1: Gmapping          | [`gmapping.launch`](ros_ws/src/robot_slam/launch/gmapping.launch), [`gmapping_params.yaml`](ros_ws/src/robot_slam/config/gmapping_params.yaml) |
| `robot_localization` | Tarea 2: AMCL              | [`amcl.launch`](ros_ws/src/robot_localization/launch/amcl.launch), [`amcl_params.yaml`](ros_ws/src/robot_localization/config/amcl_params.yaml) |
| `robot_navigation`   | Tarea 3: Navigation Stack  | [`move_base.launch`](ros_ws/src/robot_navigation/launch/move_base.launch), configs DWA/costmaps                                                |

### Parámetros consistentes con ARCHITECTURE.md

- **Robot diferencial**: chasis 0.40×0.30×0.15m, 3kg, ruedas r=0.075m, baseline=0.35m
- **LiDAR**: 270° (360 muestras), 20Hz, rango 0.1–10m, ruido gaussiano σ=0.01
- **Gmapping**: particles=80, delta=0.05, linearUpdate=1.0, angularUpdate=0.5
- **AMCL**: min_particles=500, max_particles=5000, laser_model=likelihood_field
- **Navigation**: inflation_radius=0.40, max_vel_x=0.55, sim_time=1.5, DWA con α=32, β=24, γ=0.02

## Alcance del Proyecto (Unidad 10)

Basado en el plan de estudios, el proyecto integrador comprende:

| Subsección | Descripción                                                       |
| ---------- | ----------------------------------------------------------------- |
| 10.1       | Definición del problema y diseño del robot en simulación          |
| 10.2       | Tarea 1: Mapeo con Gmapping (SLAM)                                |
| 10.3       | Tarea 2: Localización con AMCL                                    |
| 10.4       | Tarea 3: Navegación con Navigation Stack (A\* global + DWA local) |

## Stack Tecnológico

- ROS Noetic + Gazebo (vía Docker en Ubuntu 26.04)
- RViz (visualización)
- Gmapping (SLAM basado en partículas)
- AMCL (localización probabilística)
- Navigation Stack (planificador global A\* + local DWA)
- Robot móvil diferencial (URDF en Xacro)
- Pipeline secuencial: Mapa único compartido entre tareas

## Decisiones Arquitectónicas (ADRs)

| ID      | Decisión                         | Alternativa descartada   | Sustento                                                                      |
| ------- | -------------------------------- | ------------------------ | ----------------------------------------------------------------------------- |
| ADR-001 | Gmapping (Rao-Blackwellized PF)  | Hector SLAM, EKF-SLAM    | Especificación curricular + soporte odometría + mapa compatible con AMCL      |
| ADR-002 | AMCL con KLD-sampling            | EKF Localization         | Localización global y tracking; robustez ante "kidnapped robot"               |
| ADR-003 | DWA (Dynamic Window Approach)    | TEB (Timed Elastic Band) | Especificación curricular; suficiente para entorno estático                   |
| ADR-004 | Pipeline secuencial (mapa único) | Pipeline independiente   | Coherencia cross-tarea; el mapeo debe ser de calidad para no propagar errores |

## Instrucciones de uso

```bash
# 1. Iniciar contenedor
cd docker && docker compose up -d

# 2. Entrar al contenedor
docker exec -it ros_noetic_sim bash

# 3. Tarea 1: Mapeo (dentro del contenedor)
roslaunch robot_gazebo spawn_robot.launch &
roslaunch robot_slam gmapping.launch &
rosrun teleop_twist_keyboard teleop_twist_keyboard.py
# En otra terminal: rosrun map_server map_saver -f /ros_ws/src/robot_gazebo/maps/mapa_final

# 4. Tarea 2: Localización
roslaunch robot_gazebo spawn_robot.launch &
roslaunch robot_localization amcl.launch &

# 5. Tarea 3: Navegación
roslaunch robot_navigation navigation.launch &
```

## Estado final

El proyecto integrador **Simulación de Navegación Autónoma en Entornos Cerrados** ha completado todas las etapas:

1. ✅ `REQUIREMENTS.md` — Especificaciones
2. ✅ `ARCHITECTURE.md` — Blueprint técnico
3. ✅ `trabajo_tenam.tex` + `.pdf` — Documento LaTeX
4. ✅ `TEST_REPORT.md` — Verificación técnica
5. ✅ `REVIEW_REPORT.md` — Auditoría final
6. ✅ **Entorno Docker ROS Noetic + Gazebo** — Imagen compilada exitosamente
7. ✅ **5 paquetes ROS** implementados con parámetros exactos de ARCHITECTURE.md
