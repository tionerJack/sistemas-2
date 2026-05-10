# REQUIREMENTS — Proyecto Integrador: Simulación de Navegación Autónoma

> **Fuente**: Unidad 10 del Plan de Estudios — Seminario de Sistemas Inteligentes II: Robótica Móvil  
> **Propósito**: Especificaciones funcionales y técnicas para documento académico (LaTeX, 15–25 pp.)  
> **Precedencia**: [`CONTEXT.md`](CONTEXT.md) define alcance y stack. Este documento detalla requisitos.

---

## Índice de Requerimientos

| ID       | Tipo             | Descripción                                    | Prioridad |
| -------- | ---------------- | ---------------------------------------------- | --------- |
| REQ-F-01 | Funcional (10.1) | Definición del problema y diseño del robot     | Alta      |
| REQ-F-02 | Funcional (10.1) | Modelo URDF/SDF del robot diferencial          | Alta      |
| REQ-F-03 | Funcional (10.1) | Sensor LiDAR en simulación                     | Alta      |
| REQ-F-04 | Funcional (10.2) | Tarea 1: Mapeo con Gmapping                    | Alta      |
| REQ-F-05 | Funcional (10.3) | Tarea 2: Localización con AMCL                 | Alta      |
| REQ-F-06 | Funcional (10.4) | Tarea 3: Navegación con Navigation Stack       | Alta      |
| REQ-T-01 | Técnico          | Arquitectura ROS (nodos, tópicos, servicios)   | Alta      |
| REQ-T-02 | Técnico          | Fundamento teórico por tarea                   | Media     |
| REQ-T-03 | Técnico          | Configuración práctica (parámetros, launch)    | Alta      |
| REQ-T-04 | Técnico          | Análisis de resultados esperados               | Media     |
| REQ-T-05 | Técnico          | Diagrama Mermaid de arquitectura ROS           | Alta      |
| REQ-D-01 | Documental       | Formato Harvard (natbib, apalike)              | Alta      |
| REQ-D-02 | Documental       | Mínimo 10 referencias bibliográficas           | Alta      |
| REQ-D-03 | Documental       | Plantilla LaTeX existente (extender secciones) | Alta      |
| REQ-D-04 | Documental       | Extensión 15–25 páginas                        | Media     |
| REQ-V-01 | Validación       | Coherencia cross-tarea (mapa único compartido) | Alta      |

---

## 1. Requerimientos Funcionales

### 1.1 REQ-F-01: Definición del Problema y Diseño del Robot (10.1)

**Descripción**: Plantear el problema de navegación autónoma en entorno cerrado desconocido (ej. almacén, oficina). Justificar elección de robot diferencial frente a Ackerman u omnidireccional.

**Especificaciones**:

- **Tipo de robot**: Móvil diferencial (2 ruedas motrices + 1 rueda loca / rueda de apoyo)
- **Entorno**: Simulado en Gazebo, estático, con paredes, pasillos y obstáculos
- **Tarea global**: El robot debe (1) explorar y mapear → (2) localizarse → (3) navegar a un punto objetivo
- **Entregable en documento**:
  - Planteamiento del problema de SLAM (mapeo simultáneo vs. localización en mapa conocido)
  - Justificación técnica de robot diferencial (menos complejidad mecánica, control cinemático simple, adecuado para interiores)
  - Ecuaciones de cinemática directa e inversa del diferencial
  - Limitaciones: no puede moverse lateralmente, susceptible a deslizamiento

### 1.2 REQ-F-02: Modelo URDF/SDF del Robot Diferencial (10.1)

**Descripción**: Diseñar el modelo unificado del robot en formato URDF (ROS) o SDF (Gazebo).

**Especificaciones**:

- **Estructura del robot**:
  - `base_link` → chasis (caja o cilindro)
  - `left_wheel_link` → rueda izquierda (revolute joint)
  - `right_wheel_link` → rueda derecha (revolute joint)
  - `caster_wheel_link` → rueda de apoyo (fixed o continuous joint)
  - `laser_frame` → mounting del LiDAR (fixed joint)
- **Parámetros físicos** (propuestos):
  - Masa del chasis: ~2–5 kg
  - Radio de ruedas: ~0.05–0.10 m
  - Distancia entre ruedas (baseline): ~0.20–0.35 m
- **Transmisiones**: `<transmission>` para simulación en Gazebo (VeloctiyJointInterface)
- **Gazanegra**: Plugin `libgazebo_ros_diff_drive.so` para control diferencial
- **Sensor**: Plugin `libgazebo_ros_laser.so` para LiDAR

**Entregable en documento**:

- Fragmentos URDF (no el archivo completo, sino las secciones relevantes comentadas)
- Árbol de TF esperado

### 1.3 REQ-F-03: Sensor LiDAR en Simulación (10.1)

**Descripción**: Configurar un sensor LiDAR 2D en Gazebo.

**Especificaciones**:

- **Tipo**: Rayo Láser 2D (simulando Hokuyo URG-04LX o SICK LMS1xx)
- **Rango**: 0.1 – 10 m (o mayor según entorno)
- **Ángulo de apertura**: 270°–360°
- **Resolución angular**: ~1° (360 lecturas por barrido)
- **Frecuencia**: 10–40 Hz
- **Ruido**: Añadir desviación gaussiana ~0.01 m en `sensor:gazebo`
- **Entregable en documento**: Tabla de especificaciones LiDAR + fragmento SDF/URDF

### 1.4 REQ-F-04: Tarea 1 — Mapeo con Gmapping (10.2)

**Descripción**: Teleoperar el robot en el entorno simulado para construir un mapa de rejilla de ocupación mediante SLAM basado en partículas (Gmapping).

**Especificaciones**:

- **Paquete**: `gmapping` (ROS, `slam_gmapping` node)
- **Tópicos**:
  - `/scan` (sensor_msgs/LaserScan) ← entrada del LiDAR
  - `/tf` (tf/tfMessage) ← transformaciones
  - `/map` (nav_msgs/OccupancyGrid) ← salida del mapa
  - `/map_metadata` (nav_msgs/MapMetaData)
- **Parámetros clave a documentar**:
  - `particles`: número de partículas (ej. 80–100)
  - `delta`: resolución de la rejilla (ej. 0.05 m)
  - `xmin`, `ymin`, `xmax`, `ymax`: límites del mapa
  - `srr`, `srt`, `str`, `stt`: modelo de odometría
  - `linearUpdate`, `angularUpdate`: umbrales de actualización
- **Procedimiento**:
  1. Lanzar Gazebo con el entorno y el robot
  2. Lanzar `slam_gmapping`
  3. Teleoperar (`teleop_twist_keyboard` o nodo programado) cubriendo todo el entorno
  4. Guardar mapa con `map_server map_saver`
- **Análisis esperado en documento**:
  - Evaluación cualitativa: cobertura del mapa, bordes definidos, cierre de bucles
  - Evaluación cuantitativa: tiempo de exploración, tamaño del mapa, consistencia
  - Comparación teórica con Hector SLAM y EKF-SLAM

### 1.5 REQ-F-05: Tarea 2 — Localización con AMCL (10.3)

**Descripción**: Cargar el mapa guardado y ejecutar localización probabilística usando AMCL (Adaptive Monte Carlo Localization).

**Especificaciones**:

- **Paquete**: `amcl` (ROS)
- **Tópicos**:
  - `/scan` (sensor_msgs/LaserScan)
  - `/tf` (tf/tfMessage)
  - `/map` (nav_msgs/OccupancyGrid)
  - `/initialpose` (geometry_msgs/PoseWithCovarianceStamped)
  - `/amcl_pose` (geometry_msgs/PoseWithCovarianceStamped)
  - `/particlecloud` (geometry_msgs/PoseArray)
- **Parámetros clave a documentar**:
  - `min_particles`, `max_particles`: partículas mín/máx (ej. 500/5000)
  - `update_min_d`, `update_min_a`: umbrales de re-muestreo
  - `resample_interval`: intervalo de re-muestreo
  - `laser_model_type`: `likelihood_field` (recomendado para simulación)
  - `laser_z_hit`, `laser_z_rand`: pesos del modelo de sensor
  - `odom_model_type`: modelo de odometría
- **Procedimiento**:
  1. Lanzar Gazebo con entorno y robot en pose conocida
  2. Cargar mapa con `map_server map_server`
  3. Lanzar `amcl` con el mapa cargado
  4. Publicar `initialpose` con `rviz` "2D Pose Estimate"
  5. Teleoperar y observar convergencia de partículas en RViz
- **Análisis esperado**:
  - Tiempo de convergencia del filtro
  - Robustud frente a errores de odometría
  - Visualización de nube de partículas

### 1.6 REQ-F-06: Tarea 3 — Navegación con Navigation Stack (10.4)

**Descripción**: Configurar el Navigation Stack con planificador global A\* y planificador local DWA para que el robot navegue autónomamente a un punto meta.

**Especificaciones**:

- **Paquete**: `move_base` (ROS Navigation Stack)
- **Planificador global**: `navfn` / `global_planner` (A\*)
- **Planificador local**: `dwa_local_planner` (Dynamic Window Approach)
- **Tópicos**:
  - `/move_base_simple/goal` (geometry_msgs/PoseStamped)
  - `/move_base/status`, `/move_base/result`
  - `/cmd_vel` (geometry_msgs/Twist)
  - `/map` (nav_msgs/OccupancyGrid)
  - `/odom` (nav_msgs/Odometry)
- **Costmaps**:
  - `global_costmap`: mapa completo, inflación alrededor de obstáculos
  - `local_costmap`: ventana centrada en el robot, actualización frecuente
- **Parámetros clave a documentar**:
  - `max_vel_x`, `min_vel_x`: velocidades lineales
  - `max_vel_theta`, `min_vel_theta`: velocidades angulares
  - `acc_lim_x`, `acc_lim_theta`: aceleraciones
  - `goal_tolerance`: distancia angular y lineal para considerar goal alcanzado
  - `sim_time`: ventana de simulación DWA
  - `inflation_radius`: radio de inflado de obstáculos
- **Procedimiento**:
  1. Lanzar Gazebo + robot + mapa + AMCL
  2. Lanzar `move_base` con configuración de planners y costmaps
  3. Publicar goal con `rviz` "2D Nav Goal"
  4. Observar plan global + ejecución local en RViz
- **Análisis esperado**:
  - Tiempo de planificación global (A\*)
  - Suavidad de trayectoria ejecutada (DWA)
  - Capacidad de evasión de obstáculos dinámicos (si aplica)
  - Eficiencia: distancia recorrida vs. distancia ideal

---

## 2. Requerimientos Técnicos

### 2.1 REQ-T-01: Arquitectura ROS

**Descripción**: Documentar la arquitectura completa de nodos, tópicos y servicios que interactúan en el sistema integrado.

**Elementos**:

- **Nodos**: `gazebo`, `robot_state_publisher`, `slam_gmapping`, `amcl`, `move_base`, `map_server`, `rviz`, `teleop_twist_keyboard`
- **Tópicos clave**: `/scan`, `/tf`, `/tf_static`, `/map`, `/odom`, `/cmd_vel`, `/move_base_simple/goal`, `/amcl_pose`, `/particlecloud`
- **Servicios**: `/static_map`, `/request_nomotion_update`
- **Árbol TF**: `map → odom → base_footprint → base_link → laser_frame`

**Entregable**: Diagrama Mermaid de arquitectura (ver sección 5).

### 2.2 REQ-T-02: Fundamento Teórico por Tarea

**Descripción**: Cada tarea debe incluir base teórica suficiente:

| Tarea           | Fundamento obligatorio                                                                                                                                  |
| --------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 10.2 Gmapping   | Filtro de partículas (SIR), Rao-Blackwellized SLAM, re-muestreo adaptativo, modelo de probabilidad de escaneo LiDAR                                     |
| 10.3 AMCL       | Filtro de partículas adaptativo (KLD sampling), modelo de movimiento de odometría, modelo de sensor likelihood field, recuperación de fallos            |
| 10.4 Navegación | Algoritmo A\* (heurística, optimalidad, completeness), Dynamic Window Approach (espacio de velocidades, función objetivo G(v,ω)), costmaps de inflación |

### 2.3 REQ-T-03: Configuración Práctica

**Descripción**: Proveer fragmentos de configuración esenciales:

- Launch files: `gazebo.launch`, `gmapping.launch`, `amcl.launch`, `move_base.launch`
- YAML de parámetros: `costmap_common_params.yaml`, `global_costmap_params.yaml`, `local_costmap_params.yaml`, `dwa_local_planner_params.yaml`
- URDF/SDF: secciones críticas (transmissions, gazebo plugins)

### 2.4 REQ-T-04: Análisis de Resultados Esperados

**Descripción**: Cada tarea debe reportar resultados cualitativos y cuantitativos esperados:

| Tarea        | Métrica cualitativa                          | Métrica cuantitativa                                                             |
| ------------ | -------------------------------------------- | -------------------------------------------------------------------------------- |
| Mapeo        | Definición de bordes, cierre de bucles       | Cobertura (%), tiempo de exploración (s), tamaño de mapa (celdas)                |
| Localización | Convergencia de partículas, precisión visual | Error de pose (m), tiempo de convergencia (s), número de partículas              |
| Navegación   | Suavidad de trayectoria, evasión             | Tiempo de planificación (ms), longitud de ruta (m), desviación de ruta ideal (%) |

---

## 3. Requerimientos Documentales

### 3.1 REQ-D-01: Formato Harvard

**Configuración en [`trabajo_tenam.tex`](trabajo_tenam.tex:100)**:

- `bibliographystyle{apalike}` — ya incluido
- `natbib` con `authoryear` — ya incluido
- Citas en texto: `\citep{autor_año}` o `\citet{autor_año}`

### 3.2 REQ-D-02: Mínimo 10 Referencias

**Fuentes mínimas sugeridas**:

| #   | Referencia Harvard                                                                                                                                                                                                  | Tópico                           |
| --- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------- |
| 1   | Thrun, S., Burgard, W. and Fox, D. (2005) _Probabilistic Robotics_. MIT Press.                                                                                                                                      | SLAM, localización, filtros      |
| 2   | Siegwart, R., Nourbakhsh, I.R. and Scaramuzza, D. (2011) _Introduction to Autonomous Mobile Robots_. 2nd edn. MIT Press.                                                                                            | Cinemática diferencial, sensores |
| 3   | Grisetti, G., Stachniss, C. and Burgard, W. (2007) 'Improved techniques for grid mapping with Rao-Blackwellized particle filters', _IEEE Transactions on Robotics_, 23(1), pp. 34–46.                               | Gmapping                         |
| 4   | Fox, D. (2003) 'Adapting the sample size in particle filters through KLD-sampling', _International Journal of Robotics Research_, 22(12), pp. 985–1003.                                                             | AMCL (KLD sampling)              |
| 5   | Fox, D., Burgard, W. and Thrun, S. (1997) 'The dynamic window approach to collision avoidance', _IEEE Robotics & Automation Magazine_, 4(1), pp. 23–33.                                                             | DWA                              |
| 6   | Hart, P.E., Nilsson, N.J. and Raphael, B. (1968) 'A formal basis for the heuristic determination of minimum cost paths', _IEEE Transactions on Systems Science and Cybernetics_, 4(2), pp. 100–107.                 | A\*                              |
| 7   | Quigley, M. et al. (2009) 'ROS: an open-source Robot Operating System', in _Proc. IEEE International Conference on Robotics and Automation (ICRA) Workshop_.                                                        | ROS                              |
| 8   | Koenig, N. and Howard, A. (2004) 'Design and use paradigms for Gazebo, an open-source multi-robot simulator', in _Proc. IEEE/RSJ International Conference on Intelligent Robots and Systems (IROS)_, pp. 2149–2154. | Gazebo                           |
| 9   | Montemerlo, M. and Thrun, S. (2007) 'FastSLAM: a factored solution to the simultaneous localization and mapping problem', _Proc. AAAI National Conference on Artificial Intelligence_.                              | FastSLAM / Rao-Blackwellized     |
| 10  | Marder-Eppstein, E. et al. (2010) 'The office marathon: Robust navigation in an indoor office environment', in _Proc. IEEE International Conference on Robotics and Automation (ICRA)_, pp. 300–307.                | Navigation Stack                 |

### 3.3 REQ-D-03: Plantilla LaTeX

**Extensión de [`trabajo_tenam.tex`](trabajo_tenam.tex)**:

- Completar secciones vacías: `Introducción`, `Desarrollo` (con subsecciones 10.1–10.4), `Conclusiones`, `Referencias`
- NO modificar preámbulo (paquetes, colores, formato)
- Agregar sección `Desarrollo` con subsecciones anidadas:
  ```latex
  \section{Desarrollo}
  \subsection{Definición del Problema y Diseño del Robot}
  \subsubsection{Cinemática del Robot Diferencial}
  ...
  \subsection{Tarea 1: Mapeo con Gmapping}
  ...
  \subsection{Tarea 2: Localización con AMCL}
  ...
  \subsection{Tarea 3: Navegación con Navigation Stack}
  ...
  ```

### 3.4 REQ-D-04: Extensión

- 15–25 páginas en formato letter, 12pt, interlineado 1.4
- Incluir: portada, resumen, introducción, desarrollo (3 tareas), conclusiones, referencias
- Opcional: apéndice con fragmentos de código (launch, YAML, URDF)

---

## 4. Requerimientos de Validación

### 4.1 REQ-V-01: Coherencia Cross-Tarea

- El mapa generado en Tarea 1 (Gmapping) debe ser el mismo mapa cargado en Tarea 2 (AMCL) y Tarea 3 (Navigation Stack)
- Las configuraciones deben ser consistentes: misma resolución de mapa, mismo robot, mismos frames TF
- La pose inicial de AMCL debe corresponder a la última pose conocida del mapeo

---

## 5. Diagrama de Arquitectura ROS

```
flowchart TB
    subgraph Simulación["Gazebo / Simulación"]
        GAZ[Gazebo Server]
        ENV[Entorno .world]
        ROBOT[Robot URDF/SDF]
    end

    subgraph Percepción["Percepción"]
        LIDAR[LiDAR Plugin\n/gazebo_ros_laser]
        ODOM[Odometría Plugin\n/diff_drive]
    end

    subgraph TF["Sistema de TF"]
        RSP[robot_state_publisher]
        TF_TOPIC[/tf, /tf_static\]
    end

    subgraph SLAM["SLAM - Tarea 1"]
        GMAPPING[slam_gmapping\nFiltro Rao-Blackwellized]
        MAP_SERV[map_server\nGuarda: map_saver]
    end

    subgraph LOC["Localización - Tarea 2"]
        AMCL[amcl\nKLD Adaptive Particle Filter]
        PARTICLE[/particlecloud\]
        AMCL_POSE[/amcl_pose\]
    end

    subgraph NAV["Navegación - Tarea 3"]
        MOVE_BASE[move_base]
        subgraph Global["Planificador Global"]
            GLOBAL_PLANNER[navfn / A*\nglobal_planner]
            GLOBAL_COSTMAP[global_costmap]
        end
        subgraph Local["Planificador Local"]
            LOCAL_PLANNER[dwa_local_planner\nDWA]
            LOCAL_COSTMAP[local_costmap]
        end
    end

    subgraph UI["Interacción"]
        RVZ[RViz]
        TELEOP[teleop_twist_keyboard\n/ 2D Nav Goal]
        GOAL[/move_base_simple/goal\]
    end

    %% Conexiones principales
    GAZ --> ROBOT
    LIDAR --> |/scan| GMAPPING
    LIDAR --> |/scan| AMCL
    LIDAR --> |/scan| MOVE_BASE
    ODOM --> |/odom| TF_TOPIC
    ODOM --> |/odom| AMCL
    RSP --> TF_TOPIC

    TF_TOPIC --> GMAPPING
    TF_TOPIC --> AMCL
    TF_TOPIC --> MOVE_BASE

    GMAPPING --> |/map| MAP_SERV
    MAP_SERV --> |/map| AMCL
    MAP_SERV --> |/map| MOVE_BASE

    AMCL --> PARTICLE
    AMCL --> AMCL_POSE
    AMCL --> |/amcl_pose| MOVE_BASE

    MOVE_BASE --> |/cmd_vel| ROBOT
    TELEOP --> |/cmd_vel| ROBOT
    GOAL --> MOVE_BASE

    RVZ --> |/initialpose| AMCL
    RVZ --> |/move_base_simple/goal| MOVE_BASE

    %% Estilos
    classDef tarea1 fill:#d4f1f9,stroke:#0077b6
    classDef tarea2 fill:#d5f5e3,stroke:#1a7a42
    classDef tarea3 fill:#fdebd0,stroke:#b9770e
    classDef infra fill:#f0f0f0,stroke:#666
    class GMAPPING,MAP_SERV tarea1
    class AMCL,PARTICLE,AMCL_POSE tarea2
    class MOVE_BASE,GLOBAL_PLANNER,LOCAL_PLANNER,GLOBAL_COSTMAP,LOCAL_COSTMAP tarea3
    class GAZ,ENV,ROBOT,LIDAR,ODOM,RSP,TF_TOPIC infra
```

---

## 6. Estructura del Documento LaTeX

```
Portada
Resumen (Abstract)
Introducción
  - Contexto de robótica móvil y navegación autónoma
  - Objetivo del proyecto integrador
  - Organización del documento

1. Desarrollo
  1.1 Definición del Problema y Diseño del Robot (10.1)
      1.1.1 Planteamiento del problema
      1.1.2 Cinemática del robot diferencial
      1.1.3 Modelo URDF/SDF en simulación
      1.1.4 Sensor LiDAR: especificaciones y configuración
  1.2 Tarea 1: Mapeo con Gmapping (10.2)
      1.2.1 Fundamento teórico: SLAM basado en partículas
      1.2.2 Configuración del paquete gmapping
      1.2.3 Procedimiento experimental
      1.2.4 Resultados esperados
  1.3 Tarea 2: Localización con AMCL (10.3)
      1.3.1 Fundamento teórico: Filtro de partículas adaptativo
      1.3.2 Configuración del paquete amcl
      1.3.3 Procedimiento experimental
      1.3.4 Resultados esperados
  1.4 Tarea 3: Navegación con Navigation Stack (10.4)
      1.4.1 Fundamento teórico: A* y DWA
      1.4.2 Configuración de move_base y costmaps
      1.4.3 Procedimiento experimental
      1.4.4 Resultados esperados

2. Diagrama de Arquitectura del Sistema
  2.1 Nodos y tópicos ROS
  2.2 Árbol de transformaciones (TF)

3. Conclusiones

Referencias (formato Harvard, mínimo 10)

Apéndice (opcional)
  - Fragmentos de launch files
  - Parámetros YAML
  - Fragmento URDF
```

---

## 7. ADR — Decisiones Arquitectónicas

### ADR-001: Gmapping sobre Hector SLAM

| Contexto                                                                                                                             | Decisión                                                                                                                                                           | Consecuencia                                                                                                             |
| ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------ |
| El plan de estudios especifica Gmapping para la tarea de mapeo (10.2). Alternativas incluyen Hector SLAM (sin odometría) y EKF-SLAM. | Usar Gmapping (Rao-Blackwellized particle filter) porque es el estándar en ROS para interiores, soporta odometría y produce mapas de rejilla compatibles con AMCL. | Mayor precisión en interiores que Hector SLAM (que requiere LiDAR de alta frecuencia). Dependencia de odometría precisa. |

### ADR-002: AMCL sobre EKF Localization

| Contexto                                                                                                                   | Decisión                                                                                 | Consecuencia                                                                               |
| -------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| Localizacion global (no solo tracking) es necesaria para el caso de uso. AMCL maneja localización global y de seguimiento. | Usar AMCL con KLD-sampling (muestreo adaptativo) para balancear precisión y computación. | AMCL puede recuperarse del "robot secuestrado" (kidnapped robot). EKF solo tracking local. |

### ADR-003: DWA sobre TEB como planificador local

| Contexto                                                                                                                          | Decisión                                                           | Consecuencia                                                                                               |
| --------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| Plan de estudios especifica DWA para el planificador local. Alternativa: TEB (Timed Elastic Band) ofrece trayectorias más suaves. | Usar DWA (Dynamic Window Approach) según especificación académica. | Trayectorias menos suaves que TEB pero computacionalmente más eficiente. Suficiente para entorno estático. |

### ADR-004: Mapa único compartido entre tareas

| Contexto                                                                                                          | Decisión                                                                                       | Consecuencia                                                                                                        |
| ----------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Las tres tareas se ejecutan secuencialmente; el mapa de salida de Gmapping es entrada de AMCL y Navigation Stack. | El pipeline es secuencial: Mapeo → guardar mapa → cargar en AMCL → cargar en Navigation Stack. | Garantiza coherencia. Si el mapa es deficiente, las tareas 2 y 3 heredan el error. Se requiere un mapeo de calidad. |

---

## 8. Criterios de Aceptación

| ID    | Criterio                                                                    | Verificación          |
| ----- | --------------------------------------------------------------------------- | --------------------- |
| CA-01 | REQUIREMENTS.md cubre todas las subsecciones 10.1–10.4                      | Revisión de contenido |
| CA-02 | Cada tarea tiene: fundamento teórico + configuración + resultados esperados | Revisión cruzada      |
| CA-03 | Diagrama de arquitectura ROS presente                                       | Visual                |
| CA-04 | Mínimo 10 referencias en formato Harvard                                    | Conteo                |
| CA-05 | Estructura de documento compatible con plantilla existente                  | Comparación           |
| CA-06 | ADRs documentan decisiones técnicas clave                                   | Conteo (mín 4)        |
| CA-07 | Todas las referencias son a fuentes reales y verificables                   | Validación            |
