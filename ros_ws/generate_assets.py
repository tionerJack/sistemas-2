#!/usr/bin/env python3
"""Generate visual assets for ROS Noetic simulation report (headless)."""

import os
import subprocess
from PIL import Image, ImageDraw, ImageFont

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_PATH = os.path.join(OUT_DIR, "maps", "warehouse_map.pgm")
MAP_YAML = os.path.join(OUT_DIR, "maps", "warehouse_map.yaml")

# ── helpers ──────────────────────────────────────────────────────────────

def _parse_yaml(path):
    """Minimal YAML key: value parser (no deps)."""
    vals = {}
    with open(path) as f:
        for line in f:
            if ":" in line:
                k, v = line.split(":", 1)
                vals[k.strip()] = v.strip()
    return vals

def _meters_to_pixels(x_m, y_m, origin, resolution):
    """World coords → pixel coords (PGM origin is bottom-left)."""
    ox, oy = origin[0], origin[1]
    px = int((x_m - ox) / resolution)
    py = int((y_m - oy) / resolution)
    return px, py


# ── 1. PGM → PNG ────────────────────────────────────────────────────────

def convert_pgm_to_png():
    src = MAP_PATH
    dst = os.path.join(OUT_DIR, "warehouse_map.png")
    img = Image.open(src)
    # PGM loads as 'L' mode; convert to RGB with colormap
    arr = img.load()
    w, h = img.size
    rgb = Image.new("RGB", (w, h))
    pix = rgb.load()
    for y in range(h):
        for x in range(w):
            v = arr[x, y]
            if v == 205:        # unknown → light gray
                pix[x, y] = (200, 200, 200)
            elif v == 0:         # free (white in PGM)
                pix[x, y] = (255, 255, 255)
            else:                # occupied → dark / black
                g = max(0, 255 - v)
                pix[x, y] = (g, g, g)
    rgb.save(dst)
    print(f"✅ warehouse_map.png  ({w}x{h})")
    return rgb, w, h


# ── 2. Annotated map ────────────────────────────────────────────────────

def generate_annotated_map(base_img, w, h):
    meta = _parse_yaml(MAP_YAML)
    resolution = float(meta["resolution"])
    origin = [float(x) for x in meta["origin"].strip("[]").split(",")]

    dst = os.path.join(OUT_DIR, "annotated_map.png")
    canvas = base_img.copy()
    draw = ImageDraw.Draw(canvas)

    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 14)
        font_sm = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 11)
    except OSError:
        font = font_sm = ImageFont.load_default()

    # ── Origin (0,0) marker ──
    ox_p, oy_p = _meters_to_pixels(0, 0, origin, resolution)
    # flip Y: PGM origin is bottom-left, PIL origin is top-left
    oy_p = h - 1 - oy_p
    r = 6
    draw.ellipse([ox_p - r, oy_p - r, ox_p + r, oy_p + r], outline=(255, 0, 0), width=2)
    draw.text((ox_p + 10, oy_p - 10), "Origen (0,0)", fill=(255, 0, 0), font=font)

    # ── Axes ──
    # X axis (red)
    x_end = min(w - 20, ox_p + 200)
    draw.line([(ox_p, oy_p), (x_end, oy_p)], fill=(255, 0, 0), width=2)
    draw.text((x_end - 20, oy_p + 4), "X", fill=(255, 0, 0), font=font)

    # Y axis (green)
    y_end = max(20, oy_p - 200)
    draw.line([(ox_p, oy_p), (ox_p, y_end)], fill=(0, 180, 0), width=2)
    draw.text((ox_p + 4, y_end - 4), "Y", fill=(0, 180, 0), font=font)

    # ── Tick marks every 2 meters ──
    step_m = 2.0
    step_px = int(step_m / resolution)
    for i in range(0, w, step_px):
        # X ticks
        world_x = origin[0] + i * resolution
        tick_x = i
        tick_y = oy_p
        if 0 <= tick_x < w:
            draw.line([(tick_x, tick_y - 4), (tick_x, tick_y + 4)], fill=(100, 100, 100), width=1)
            if abs(world_x) < 0.01 or i % (step_px * 2) == 0:
                draw.text((tick_x - 10, tick_y + 6), f"{world_x:.0f}", fill=(80, 80, 80), font=font_sm)
    for j in range(0, h, step_px):
        # Y ticks
        world_y = origin[1] + j * resolution
        tick_x = ox_p
        tick_y = h - 1 - j
        if 0 <= tick_y < h:
            draw.line([(tick_x - 4, tick_y), (tick_x + 4, tick_y)], fill=(100, 100, 100), width=1)
            if abs(world_y) < 0.01 or j % (step_px * 2) == 0:
                draw.text((tick_x + 6, tick_y - 7), f"{world_y:.0f}", fill=(80, 80, 80), font=font_sm)

    # ── Legend ──
    leg_x, leg_y = 10, 10
    draw.rectangle([leg_x, leg_y, leg_x + 180, leg_y + 70], fill=(255, 255, 255), outline=(0, 0, 0))
    draw.text((leg_x + 5, leg_y + 2), "Leyenda", fill=(0, 0, 0), font=font)
    draw.rectangle([leg_x + 5, leg_y + 22, leg_x + 25, leg_y + 42], fill=(255, 255, 255))
    draw.text((leg_x + 30, leg_y + 22), "Libre (explorado)", fill=(0, 0, 0), font=font_sm)
    draw.rectangle([leg_x + 5, leg_y + 44, leg_x + 25, leg_y + 64], fill=(200, 200, 200))
    draw.text((leg_x + 30, leg_y + 44), "No explorado", fill=(0, 0, 0), font=font_sm)

    canvas.save(dst)
    print(f"✅ annotated_map.png  ({w}x{h})")
    return canvas


# ── 3. ROS pipeline diagram (Graphviz DOT → PNG) ────────────────────────

def generate_pipeline_diagram():
    dot_src = """digraph ROS_Pipeline {
    rankdir=LR;
    splines=polyline;
    nodesep=0.8;
    ranksep=1.2;
    bgcolor="white";
    pad=0.5;

    node [shape=box, style="filled,rounded", fontname="Helvetica", fontsize=11];
    edge [fontname="Helvetica", fontsize=9];

    // ── Nodos ──
    gazebo [label="Gazebo\n(gazebo-server)", fillcolor="#AED6F1", shape=cylinder];
    gmapping [label="slam_gmapping\nT1: Mapping", fillcolor="#A9DFBF"];
    amcl [label="amcl\nT2: Localization", fillcolor="#F9E79F"];
    move_base [label="move_base\nT3: Navigation", fillcolor="#F5B7B1"];

    // Tópicos
    scan [label="/scan\nLaserScan", shape=note, fillcolor="#E8DAEF"];
    tf [label="/tf\ntfMessage", shape=note, fillcolor="#E8DAEF"];
    map [label="/map\nOccupancyGrid", shape=note, fillcolor="#E8DAEF"];
    amcl_pose [label="/amcl_pose\nPoseWithCovariance", shape=note, fillcolor="#E8DAEF"];
    cmd_vel [label="/cmd_vel\nTwist", shape=note, fillcolor="#E8DAEF"];
    goal [label="/move_base_simple/goal\nPoseStamped", shape=note, fillcolor="#E8DAEF"];

    // ── Conexiones ──
    gazebo -> scan [label="LiDAR ray", color="#2980B9"];
    scan -> gmapping [label="scan", color="#2980B9"];
    scan -> amcl [label="scan", color="#2980B9"];
    scan -> move_base [label="scan", color="#2980B9"];

    gazebo -> tf [label="diff_drive\nRSP", color="#7D3C98"];
    tf -> gmapping [label="tf", color="#7D3C98"];
    tf -> amcl [label="tf", color="#7D3C98"];
    tf -> move_base [label="tf", color="#7D3C98"];

    gmapping -> map [label="generated", color="#1E8449"];
    map -> amcl [label="loaded", color="#1E8449"];
    map -> move_base [label="loaded", color="#1E8449"];

    amcl -> amcl_pose [label="estimated pose", color="#B7950B"];
    amcl_pose -> move_base [label="pose", color="#B7950B"];

    goal -> move_base [label="2D Nav Goal", color="#C0392B", style=dashed];

    move_base -> cmd_vel [label="velocity cmd", color="#C0392B"];
    cmd_vel -> gazebo [label="diff_drive", color="#C0392B", style=bold];

    // ── Clusters por tarea ──
    subgraph cluster_T1 {
        label="Tarea 1: Mapping";
        style=dashed;
        color="#1E8449";
        gmapping;
    }
    subgraph cluster_T2 {
        label="Tarea 2: Localization";
        style=dashed;
        color="#B7950B";
        amcl;
    }
    subgraph cluster_T3 {
        label="Tarea 3: Navigation";
        style=dashed;
        color="#C0392B";
        move_base;
    }
}"""
    dot_path = os.path.join(OUT_DIR, "ros_pipeline.dot")
    png_path = os.path.join(OUT_DIR, "ros_pipeline_diagram.png")
    with open(dot_path, "w") as f:
        f.write(dot_src)
    subprocess.run(["dot", "-Tpng", dot_path, "-o", png_path], check=True)
    print(f"✅ ros_pipeline_diagram.png")
    os.remove(dot_path)


# ── Main ────────────────────────────────────────────────────────────────

def main():
    print("=" * 50)
    print("Generating report assets (headless)...")
    print("=" * 50)

    # 1. PGM → PNG
    rgb_img, w, h = convert_pgm_to_png()

    # 2. Annotated map
    generate_annotated_map(rgb_img, w, h)

    # 3. ROS pipeline diagram
    generate_pipeline_diagram()

    print("=" * 50)
    print("All assets generated successfully!")
    print(f"  {os.path.join(OUT_DIR, 'warehouse_map.png')}")
    print(f"  {os.path.join(OUT_DIR, 'annotated_map.png')}")
    print(f"  {os.path.join(OUT_DIR, 'ros_pipeline_diagram.png')}")
    print("=" * 50)


if __name__ == "__main__":
    main()
