# TEST_REPORT — Verificación de Coherencia Técnica

> **Documento**: [`trabajo_tenam.tex`](trabajo_tenam.tex) (1022 líneas)
> **PDF**: [`trabajo_tenam.pdf`](trabajo_tenam.pdf) (26 páginas, 371 KB)
> **Referencias**: [`ARCHITECTURE.md`](ARCHITECTURE.md) · [`REQUIREMENTS.md`](REQUIREMENTS.md)
> **Verificador**: 🪲 Debugger · **Fecha**: 2026-05-09

---

## 1. Compilación ✅/❌

| Item                                    | Estado | Evidencia                                                                                                                                                                                                                             |
| --------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `pdflatex` sin errores                  | ✅     | Exit code 0. PDF generado (26 pp., 371231 bytes)                                                                                                                                                                                      |
| Sin warnings críticos                   | ⚠️     | 1 warning: `destination with same identifier (name{page.1}) duplicate ignored` — línea 652 del log. Causa: `titlepage` + `\setcounter{page}{1}` generan page.1 duplicado. Cosmético, no afecta contenido.                             |
| Referencias cruzadas `\ref{}` resueltas | ✅     | 28 referencias cruzadas, todas con `\label{}` correspondiente. Sin "undefined references" en el log.                                                                                                                                  |
| Citas bibliográficas resueltas          | ⚠️     | 2 `\bibitem` sin uso en texto: [`rublee2011orb`](trabajo_tenam.tex:935) (ORB-SLAM) y [`lynch2017modern`](trabajo_tenam.tex:938) (Modern Robotics). Aparecen en bibliografía pero nunca son referenciadas con `\citep{}` o `\citet{}`. |

**Veredicto compilación**: ✅ Aceptable (1 warning cosmético + 2 referencias no citadas)

---

## 2. Contenido técnico ✅/❌

### 2.1 §10.1 — Cinemática diferencial

| Elemento                     | Estado | Líneas                             | Verificación                                                                                             |
| ---------------------------- | ------ | ---------------------------------- | -------------------------------------------------------------------------------------------------------- |
| Cinemática directa           | ✅     | [`258–266`](trabajo_tenam.tex:258) | `v = (ω_r + ω_l)·r/2`, `ω = (ω_r − ω_l)·r/L`. Coincide con [`ARCHITECTURE.md §1.5`](ARCHITECTURE.md:178) |
| Jacobiano                    | ✅     | [`270–285`](trabajo_tenam.tex:270) | Matriz `[r/2, r/2; r/L, -r/L]`. Correcta.                                                                |
| Cinemática inversa           | ✅     | [`289–293`](trabajo_tenam.tex:289) | `ω_r = (2v + ωL)/(2r)`, `ω_l = (2v − ωL)/(2r)`. Correcta.                                                |
| Parámetros físicos           | ✅     | [`297–314`](trabajo_tenam.tex:297) | r=0.075m, L=0.35m, m=3.0kg. Dentro de rangos REQ-F-02.                                                   |
| Limitaciones del diferencial | ✅     | [`318–331`](trabajo_tenam.tex:318) | Sin movimiento lateral, deslizamiento, singularidad v=0. Correcto.                                       |
| Modelo URDF                  | ✅     | [`336–386`](trabajo_tenam.tex:336) | 5 links, 4 joints. Coincide con ARCHITECTURE.md §1.1.                                                    |
| Transmisión URDF             | ✅     | [`375–386`](trabajo_tenam.tex:375) | `VelocityJointInterface`, `SimpleTransmission`. Correcto.                                                |
| Sensor LiDAR                 | ✅     | [`391–447`](trabajo_tenam.tex:391) | 180° (configurable 270°), 360 muestras, 20Hz, σ=0.01m. Coincide con ARCHITECTURE.md §1.4.                |

### 2.2 §10.2 — Parámetros Gmapping (RBPF)

| Elemento                                 | Estado | Líneas                             | Verificación                                                            |
| ---------------------------------------- | ------ | ---------------------------------- | ----------------------------------------------------------------------- | ----------- | --------- | -------------------------------------------------- |
| Ecuación RBPF                            | ✅     | [`461–464`](trabajo_tenam.tex:461) | `p(x\_{1:t}, m                                                          | z, u) = p(m | x, z)·p(x | z, u)` — factorización Rao-Blackwellized correcta. |
| `particles=80`                           | ✅     | [`489`](trabajo_tenam.tex:489)     | Rango típico 20–100. Suficiente para 10×10m.                            |
| `delta=0.05`                             | ✅     | [`490`](trabajo_tenam.tex:490)     | 5 cm/celda → 200×200 celdas. Correcto.                                  |
| `srr/srt/str/stt`                        | ✅     | [`493–496`](trabajo_tenam.tex:493) | Modelo de odometría probabilístico. Coherente con ARCHITECTURE.md §3.1. |
| `linearUpdate=1.0` / `angularUpdate=0.5` | ✅     | [`497–498`](trabajo_tenam.tex:497) | Coherente con teoría RBPF.                                              |
| `maxUrange=8.0` < `maxRange=10.0`        | ✅     | [`501`](trabajo_tenam.tex:501)     | Consistente: rango de mapa < rango del sensor.                          |
| `resampleThreshold=0.5`                  | ✅     | [`500`](trabajo_tenam.tex:500)     | `N_eff/N < 0.5` → remuestreo. Correcto para SIR.                        |

**Veredicto Gmapping**: ✅ Coherente con teoría RBPF y ARCHITECTURE.md.

### 2.3 §10.3 — Parámetros AMCL (KLD-sampling)

| Elemento                                   | Estado | Líneas                             | Verificación                                          |
| ------------------------------------------ | ------ | ---------------------------------- | ----------------------------------------------------- |
| Ecuación KLD                               | ✅     | [`574–577`](trabajo_tenam.tex:574) | `n = χ²/(2ε)`. Correcta.                              |
| `min_particles=500` / `max_particles=5000` | ✅     | [`605–606`](trabajo_tenam.tex:605) | Rango típico KLD. Coherente con Fox (2003).           |
| `kld_err=0.01`, `kld_z=0.99`               | ✅     | [`607–608`](trabajo_tenam.tex:607) | ε=0.01, δ=0.99. Valores estándar.                     |
| `laser_model_type=likelihood_field`        | ✅     | [`618`](trabajo_tenam.tex:618)     | Recomendado para simulación. ADR-006 coherente.       |
| `laser_z_hit=0.95` / `laser_z_rand=0.05`   | ✅     | [`619–620`](trabajo_tenam.tex:619) | Alta confianza en simulación. Correcto.               |
| `odom_alpha1-5`                            | ✅     | [`613–617`](trabajo_tenam.tex:613) | α₁₋₄=0.2, α₅=0.1. Coherente con ARCHITECTURE.md §4.1. |
| `recovery_alpha_slow/fast`                 | ✅     | [`626–627`](trabajo_tenam.tex:626) | 0.001 / 0.1. Relación 1:100 típica.                   |

**Veredicto AMCL**: ✅ Coherente con teoría KLD-sampling y ARCHITECTURE.md.

### 2.4 §10.4 — Configuración A\* y DWA

| Elemento                                          | Estado | Líneas                             | Verificación                               |
| ------------------------------------------------- | ------ | ---------------------------------- | ------------------------------------------ |
| Ecuación A\* `f(n)=g(n)+h(n)`                     | ✅     | [`678–681`](trabajo_tenam.tex:678) | Correcta. Heurística euclidiana admisible. |
| `use_dijkstra=false` → A\*                        | ✅     | [`695`](trabajo_tenam.tex:695)     | Correcto: false = A\*, true = Dijkstra.    |
| Ecuación DWA `G(v,ω)`                             | ✅     | [`711–713`](trabajo_tenam.tex:711) | `α·path + β·goal + γ·occ`. Correcta.       |
| `α=32, β=24, γ=0.02`                              | ✅     | [`719–721`](trabajo_tenam.tex:719) | Coincide con ARCHITECTURE.md §5.3.         |
| `max_vel_x=0.55` m/s                              | ✅     | [`735`](trabajo_tenam.tex:735)     | Velocidad moderada para interiores.        |
| `inflation_radius=0.40` m                         | ✅     | [`768`](trabajo_tenam.tex:768)     | Coherente con ARCHITECTURE.md §5.1.        |
| `global_frame: map` / local: `odom`               | ✅     | [`787`](trabajo_tenam.tex:787)     | Correcto según arquitectura ROS.           |
| `rolling_window: false` (global) / `true` (local) | ✅     | [`792–793`](trabajo_tenam.tex:792) | ADR-007 coherente.                         |

**Veredicto Navigation Stack**: ✅ Coherente con teoría A\*/DWA y ARCHITECTURE.md.

### 2.5 Diagrama de arquitectura ROS

| Elemento                     | Estado | Líneas                             | Verificación                                                                                                        |
| ---------------------------- | ------ | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| Nodos y tópicos              | ✅     | [`833–855`](trabajo_tenam.tex:833) | Tabla completa con 12 tópicos. Coincide con ARCHITECTURE.md §2.3.                                                   |
| Diagrama Mermaid renderizado | ❌     | [`825–831`](trabajo_tenam.tex:825) | **Placeholder de texto**: `\fbox{\parbox{...}{Nota: Incluir diagrama Mermaid renderizado...}}`. No hay imagen real. |
| Servicios                    | ✅     | Mencionados en tabla               | `/static_map`, `/request_nomotion_update`.                                                                          |

### 2.6 Árbol TF

| Transformación                                     | Estado | Línea                              | Verificación |
| -------------------------------------------------- | ------ | ---------------------------------- | ------------ |
| `map → odom` (amcl, variable)                      | ✅     | [`869`](trabajo_tenam.tex:869)     | Correcto     |
| `odom → base_footprint` (RSP+diff_drive, variable) | ✅     | [`870`](trabajo_tenam.tex:870)     | Correcto     |
| `base_footprint → base_link` (fixed, z=0.075)      | ✅     | [`871`](trabajo_tenam.tex:871)     | Correcto     |
| `base_link → laser_frame` (fixed, x=0.15, z=0.08)  | ✅     | [`872`](trabajo_tenam.tex:872)     | Correcto     |
| `base_link → left/right_wheel_link` (variable)     | ✅     | [`873–874`](trabajo_tenam.tex:873) | Correcto     |
| `base_link → caster_wheel_link` (fixed)            | ✅     | [`875`](trabajo_tenam.tex:875)     | Correcto     |

**Veredicto TF**: ✅ Árbol correcto, coincide con [`ARCHITECTURE.md §2.2`](ARCHITECTURE.md:313).

---

## 3. Formato académico ✅/❌

| Item                         | Estado | Evidencia                                                                                                                                                                                                                     |
| ---------------------------- | ------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Formato Harvard (`\citep{}`) | ✅     | [`26`](trabajo_tenam.tex:26) · Natbib + `apalike`. 20 llamadas `\citep`/`\citet` en el texto.                                                                                                                                 |
| Mínimo 10 referencias        | ✅     | 12 referencias en `thebibliography`.                                                                                                                                                                                          |
| Referencias no citadas       | ⚠️     | [`rublee2011orb`](trabajo_tenam.tex:935) (ORB-SLAM) y [`lynch2017modern`](trabajo_tenam.tex:938) (Modern Robotics) definidas pero sin `\citep` en el texto. No generan error de compilación pero son referencias "huérfanas". |
| Estructura de secciones      | ✅     | Portada → Resumen → Introducción → Desarrollo (§1.1–1.4) → Arquitectura (§2.1–2.2) → Conclusiones → Referencias → Apéndice. Coincide con [`REQUIREMENTS.md §6`](REQUIREMENTS.md:388).                                         |
| Portada con datos correctos  | ⚠️     | [`135`](trabajo_tenam.tex:135) · `[Nombre del Profesor]` sin reemplazar. Placeholder visible.                                                                                                                                 |
| Extensión (15–25 pp.)        | ⚠️     | 26 páginas → supera el límite superior por 1 página.                                                                                                                                                                          |

---

## 4. Correspondencia con requisitos ✅/❌

### REQ-F (Funcionales)

| ID       | Descripción                                | Estado | Localización                                                                                                          |
| -------- | ------------------------------------------ | ------ | --------------------------------------------------------------------------------------------------------------------- |
| REQ-F-01 | Definición del problema y diseño del robot | ✅     | [`§1.1`](trabajo_tenam.tex:243) · Planteamiento, justificación diferencial, cinemática directa/inversa, limitaciones. |
| REQ-F-02 | Modelo URDF/SDF del robot diferencial      | ✅     | [`§1.1.3`](trabajo_tenam.tex:333) · Links, joints, transmisiones.                                                     |
| REQ-F-03 | Sensor LiDAR en simulación                 | ✅     | [`§1.1.4`](trabajo_tenam.tex:388) · Especificaciones, plugin Gazebo.                                                  |
| REQ-F-04 | Tarea 1: Mapeo con Gmapping                | ✅     | [`§1.2`](trabajo_tenam.tex:452) · Teoría RBPF, parámetros, procedimiento, resultados.                                 |
| REQ-F-05 | Tarea 2: Localización con AMCL             | ✅     | [`§1.3`](trabajo_tenam.tex:565) · Teoría KLD, parámetros, procedimiento, resultados.                                  |
| REQ-F-06 | Tarea 3: Navegación con Navigation Stack   | ✅     | [`§1.4`](trabajo_tenam.tex:671) · A\*, DWA, costmaps, parámetros, procedimiento, resultados.                          |

### REQ-T (Técnicos)

| ID       | Descripción                                  | Estado | Evidencia                                                                                                                                                |
| -------- | -------------------------------------------- | ------ | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| REQ-T-01 | Arquitectura ROS (nodos, tópicos, servicios) | ✅     | [`§2`](trabajo_tenam.tex:818) · Tabla de 12 tópicos + TF tree.                                                                                           |
| REQ-T-02 | Fundamento teórico por tarea                 | ✅     | RBPF ([`461`](trabajo_tenam.tex:461)), KLD ([`574`](trabajo_tenam.tex:574)), A\* ([`678`](trabajo_tenam.tex:678)), DWA ([`711`](trabajo_tenam.tex:711)). |
| REQ-T-03 | Configuración práctica                       | ✅     | Fragmentos URDF ([`375`](trabajo_tenam.tex:375)), YAML costmaps ([`976`](trabajo_tenam.tex:976)), DWA ([`999`](trabajo_tenam.tex:999)).                  |
| REQ-T-04 | Análisis de resultados esperados             | ✅     | Cada tarea incluye subsección de resultados esperados.                                                                                                   |
| REQ-T-05 | Diagrama Mermaid de arquitectura ROS         | ❌     | [`825–831`](trabajo_tenam.tex:825) · **No hay diagrama renderizado**, solo un `\fbox{}` con texto descriptivo.                                           |

### REQ-D (Documentales)

| ID       | Descripción                                    | Estado | Evidencia                                                          |
| -------- | ---------------------------------------------- | ------ | ------------------------------------------------------------------ |
| REQ-D-01 | Formato Harvard (natbib, apalike)              | ✅     | [`26`](trabajo_tenam.tex:26) y [`150–151`](trabajo_tenam.tex:150). |
| REQ-D-02 | Mínimo 10 referencias bibliográficas           | ✅     | 12 referencias.                                                    |
| REQ-D-03 | Plantilla LaTeX existente (extender secciones) | ✅     | No modifica preámbulo. Extiende con secciones nuevas.              |
| REQ-D-04 | Extensión 15–25 páginas                        | ⚠️     | 26 páginas → supera por 1 página.                                  |

### REQ-V

| ID       | Descripción                                    | Estado | Evidencia                                                                                              |
| -------- | ---------------------------------------------- | ------ | ------------------------------------------------------------------------------------------------------ |
| REQ-V-01 | Coherencia cross-tarea (mapa único compartido) | ✅     | Pipeline secuencial: Gmapping → guardar mapa → cargar en AMCL → cargar en move_base. Mismos frames TF. |

---

## 5. Resumen de hallazgos

### ❌ Errores (requieren corrección)

| #   | Severidad | Descripción                                                                            | Archivo/Línea                                        | Corrección propuesta                                                                                                                                                                                                                                |
| --- | --------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| E1  | **Alta**  | Diagrama Mermaid de arquitectura ROS no renderizado. Solo hay un placeholder de texto. | [`trabajo_tenam.tex:825–831`](trabajo_tenam.tex:825) | Reemplazar el `\fbox{\parbox{...}{Nota:...}}` con una imagen del diagrama Mermaid exportado como PNG/PDF, o usar el paquete `mermaid`/`inkscape` para incluir el diagrama. El código Mermaid está en [`ARCHITECTURE.md §2.1`](ARCHITECTURE.md:217). |
| E2  | **Media** | Nombre del profesor sin reemplazar (placeholder).                                      | [`trabajo_tenam.tex:135`](trabajo_tenam.tex:135)     | Remplazar `[Nombre del Profesor]` por el nombre real.                                                                                                                                                                                               |

### ⚠️ Advertencias (recomendaciones)

| #   | Descripción                                                                                  | Archivo/Línea                                | Recomendación                                                                                                                                                                   |
| --- | -------------------------------------------------------------------------------------------- | -------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| W1  | 2 referencias en `thebibliography` nunca citadas en el texto.                                | [`935–939`](trabajo_tenam.tex:935)           | Agregar `\citep{rublee2011orb}` en alguna sección (ej. trabajo futuro, línea 894) y `\citep{lynch2017modern}` en cinemática (ej. línea 256) O eliminarlas si no son necesarias. |
| W2  | Extensión: 26 páginas (límite: 25).                                                          | PDF completo                                 | Reducir ligeramente el apéndice o ajustar espaciado. Opcional: reducir listings de YAML.                                                                                        |
| W3  | Warning de compilación: `destination with same identifier (name{page.1}) duplicate ignored`. | [`trabajo_tenam.log:652`](trabajo_tenam.log) | Agregar `\pagenumbering{arabic}` después de `\newpage\setcounter{page}{1}` (línea 203) o usar `\thispagestyle{empty}` en la titlepage.                                          |

### ✅ Aciertos

- Cinemática diferencial completa y correcta (directa, inversa, jacobiano).
- Parámetros Gmapping coherentes con teoría RBPF y literatura (Grisetti et al., 2007).
- Parámetros AMCL coherentes con KLD-sampling (Fox, 2003).
- Configuración A\* y DWA técnicamente correcta y alineada con ARCHITECTURE.md.
- Árbol TF correcto: `map → odom → base_footprint → base_link → laser_frame`.
- Tabla de tópicos ROS completa (12 tópicos, tipos, publicadores/suscriptores).
- Citas en formato Harvard con natbib + apalike.
- 20 citas distribuidas en todo el documento.
- Pipeline secuencial y coherencia cross-tarea (REQ-V-01).

---

## 6. Conclusión final

| Dominio                        | ✅/❌ | Precisión                                     |
| ------------------------------ | ----- | --------------------------------------------- |
| Compilación                    | ✅    | 1 warning cosmético, sin errores              |
| Contenido técnico (§10.1–10.4) | ✅    | Cinemática, Gmapping, AMCL, A\*/DWA correctos |
| Diagrama de arquitectura       | ❌    | **E1**: Placeholder, no renderizado           |
| Árbol TF                       | ✅    | Correcto                                      |
| Formato académico              | ⚠️    | **E2**: Profesor placeholder; **W2**: 26 pp.  |
| Referencias                    | ⚠️    | **W1**: 2 no citadas                          |
| Cobertura REQ-F (6/6)          | ✅    | 6/6 funcionales cubiertos                     |
| Cobertura REQ-T (5/5)          | ⚠️    | 4/5 técnicos cubiertos. **REQ-T-05** ❌       |
| Cobertura REQ-D (4/4)          | ⚠️    | 3/4 + 1 con salvedad                          |

**Estado global**: 🟡 **APROBADO CON OBSERVACIONES**

Se requieren **2 correcciones** (E1, E2) antes de considerar el documento listo para entrega. Las **3 advertencias** (W1, W2, W3) son recomendaciones de calidad.
