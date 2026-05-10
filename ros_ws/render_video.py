#!/usr/bin/env python3
"""Render ROS simulation videos from PGM map — no ROS / bag dependencies.

Usage:
  python3 render_video.py --type mapping   --duration 20 --fps 10 --output videos/
  python3 render_video.py --type localization --duration 20 --fps 10 --output videos/
  python3 render_video.py --type navigation --duration 20 --fps 10 --goal-x 5 --goal-y 3
"""

import argparse
import math
import os
import subprocess
import sys
import tempfile
import shutil
import random
from collections import defaultdict

from PIL import Image, ImageDraw, ImageFont

# ── paths ──────────────────────────────────────────────────────────────────
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MAP_DIR = os.path.join(SCRIPT_DIR, "maps")
MAP_PGM = os.path.join(MAP_DIR, "warehouse_map.pgm")
MAP_YAML = os.path.join(MAP_DIR, "warehouse_map.yaml")

# ── pre-loaded map cache ───────────────────────────────────────────────────
_map_data = None   # flat list of PGM values
_map_rgb_base = None  # pre-rendered RGB Image
_map_w = _map_h = 0
_map_resolution = 0.05
_map_origin = (-15.0, -15.0)


def _parse_yaml(path):
    vals = {}
    with open(path) as f:
        for line in f:
            if ":" in line:
                k, _, v = line.partition(":")
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                vals[k] = v
    return vals


def _load_map():
    """Load PGM + YAML once, cache globally."""
    global _map_data, _map_rgb_base, _map_w, _map_h, _map_resolution, _map_origin
    if _map_data is not None:
        return
    img = Image.open(MAP_PGM)
    _map_w, _map_h = img.size
    _map_data = list(img.getdata())
    # Build RGB base once
    rgb = Image.new("RGB", (_map_w, _map_h), (255, 255, 255))
    pix = rgb.load()
    for y in range(_map_h):
        for x in range(_map_w):
            v = _map_data[y * _map_w + x]
            if v == 0:
                pix[x, y] = (40, 40, 40)
            elif v == 205:
                pix[x, y] = (200, 200, 200)
            else:
                pix[x, y] = (245, 245, 245)
    _map_rgb_base = rgb
    # Parse YAML
    meta = _parse_yaml(MAP_YAML)
    _map_resolution = float(meta.get("resolution", 0.05))
    origin_str = meta.get("origin", "-15.0 -15.0 0")
    origin_str = origin_str.replace("[", "").replace("]", "").replace(",", " ")
    parts = origin_str.split()
    _map_origin = (float(parts[0]), float(parts[1]))


def _world_to_pixel(x_m, y_m):
    """World → pixel (row, col)."""
    px = int((x_m - _map_origin[0]) / _map_resolution)
    py = int((y_m - _map_origin[1]) / _map_resolution)
    return py, px


def _pixel_to_world(px, py):
    """Pixel → world."""
    x_m = py * _map_resolution + _map_origin[0]
    y_m = (_map_h - px) * _map_resolution + _map_origin[1]
    return x_m, y_m


def _render_partial_map(fraction):
    """Return RGB image with right portion masked as unknown (fast crop-based)."""
    w, h = _map_w, _map_h
    rgb = _map_rgb_base.copy()
    reveal_col = int(w * fraction)
    if reveal_col < w:
        # Overlay unknown (gray) rectangle on unrevealed area
        draw = ImageDraw.Draw(rgb)
        draw.rectangle([reveal_col, 0, w - 1, h - 1], fill=(200, 200, 200))
        # Re-draw obstacles that were covered
        pix = rgb.load()
        for y in range(h):
            for x in range(reveal_col, w):
                v = _map_data[y * w + x]
                if v == 0:
                    pix[x, y] = (40, 40, 40)
    return rgb


# ── pose generators ────────────────────────────────────────────────────────

def _generate_poses_t1(total_frames):
    """Lawnmower pattern."""
    poses = []
    x_min, x_max = -12.0, 12.0
    y_min, y_max = -12.0, 12.0
    rows = 8
    row_spacing = (y_max - y_min) / rows
    steps_per_row = max(2, total_frames // rows)
    for i in range(rows):
        y = y_min + i * row_spacing
        if i % 2 == 0:
            xs = [x_min + (x_max - x_min) * j / steps_per_row for j in range(steps_per_row)]
            yaw = 0.0
        else:
            xs = [x_max - (x_max - x_min) * j / steps_per_row for j in range(steps_per_row)]
            yaw = math.pi
        for x in xs:
            poses.append((x, y, yaw))
    while len(poses) < total_frames:
        poses.append(poses[-1])
    return poses[:total_frames]


def _generate_poses_t2(total_frames):
    """Waypoint path through corridors."""
    waypoints = [
        (-10.0, -10.0, 0.0), (-5.0, -10.0, 0.0),
        (0.0, -8.0, math.pi / 4), (5.0, -5.0, math.pi / 2),
        (8.0, 0.0, math.pi / 2), (10.0, 5.0, math.pi),
        (5.0, 8.0, -math.pi / 2), (0.0, 10.0, -math.pi / 2),
        (-5.0, 8.0, math.pi), (-8.0, 3.0, -math.pi / 2),
        (-10.0, -3.0, 0.0), (-10.0, -8.0, 0.0),
    ]
    poses = []
    segments = max(1, len(waypoints) - 1)
    frames_per_seg = max(2, total_frames // segments)
    for seg in range(segments):
        x0, y0, yaw0 = waypoints[seg]
        x1, y1, yaw1 = waypoints[seg + 1]
        for j in range(frames_per_seg):
            t = j / frames_per_seg
            poses.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t, yaw0 + (yaw1 - yaw0) * t))
    while len(poses) < total_frames:
        poses.append(poses[-1])
    return poses[:total_frames]


def _generate_poses_t3(total_frames, goal):
    """Start→goal with smooth accel/decel."""
    sx, sy = -10.0, -10.0
    gx, gy = goal
    poses = []
    for i in range(total_frames):
        t = i / max(1, total_frames - 1)
        t_ease = t * t * (3 - 2 * t)
        x = sx + (gx - sx) * t_ease
        y = sy + (gy - sy) * t_ease
        dx, dy = gx - sx, gy - sy
        goal_yaw = math.atan2(dy, dx) if abs(dx) > 0.01 or abs(dy) > 0.01 else 0.0
        poses.append((x, y, goal_yaw * t_ease))
    return poses


def _generate_particles(robot_x, robot_y, robot_yaw, num=80, spread=1.0):
    """Synthetic AMCL particle cloud."""
    return [(robot_x + random.random() * spread * math.cos(random.random() * 2 * math.pi),
             robot_y + random.random() * spread * math.sin(random.random() * 2 * math.pi),
             robot_yaw + (random.random() - 0.5) * 0.5) for _ in range(num)]


def _generate_path_wp(start, goal):
    """A*-like waypoints."""
    return [(-10.0, -10.0), (-6.0, -9.0), (-2.0, -7.0), (1.0, -4.0),
            (3.0, -1.0), (4.0, 1.0), goal]


# ── laser simulation ───────────────────────────────────────────────────────

def _simulate_laser(robot_x, robot_y, robot_yaw, max_range=8.0, num_rays=180, fov_deg=270):
    """Ray-trace laser scan. Returns (ranges, angles)."""
    ranges = []
    angles = []
    ang_step = math.radians(fov_deg / num_rays)
    start_ang = -math.radians(fov_deg / 2)
    step = _map_resolution * 4  # 4 cells per step for speed
    for i in range(num_rays):
        theta = robot_yaw + start_ang + i * ang_step
        dx = math.cos(theta)
        dy = math.sin(theta)
        dist = 0.0
        hit = False
        while dist < max_range:
            dist += step
            wx = robot_x + dist * dx
            wy = robot_y + dist * dy
            px = int((wx - _map_origin[0]) / _map_resolution)
            py = int((wy - _map_origin[1]) / _map_resolution)
            if px < 0 or px >= _map_w or py < 0 or py >= _map_h:
                dist = max_range
                break
            if _map_data[py * _map_w + px] == 0:
                hit = True
                break
        ranges.append(dist if hit else max_range)
        angles.append(theta - robot_yaw)
    return ranges, angles


# ── cost map (lazy) ────────────────────────────────────────────────────────

_cost_map = None

def _get_cost_map():
    """Generate inflated cost map once."""
    global _cost_map
    if _cost_map is not None:
        return _cost_map
    w, h = _map_w, _map_h
    cost = [[0] * w for _ in range(h)]
    inflate = 10
    obstacle_cells = [(x, y) for y in range(h) for x in range(w)
                      if _map_data[y * w + x] == 0]
    for ox, oy in obstacle_cells:
        cost[oy][ox] = 100
        for dy in range(-inflate, inflate + 1):
            for dx in range(-inflate, inflate + 1):
                nx, ny = ox + dx, oy + dy
                if 0 <= nx < w and 0 <= ny < h:
                    d = math.sqrt(dx * dx + dy * dy)
                    if d <= inflate:
                        val = max(0, 100 - int(d / inflate * 100))
                        if val > cost[ny][nx]:
                            cost[ny][nx] = val
    _cost_map = cost
    return cost


# ── drawing helpers ────────────────────────────────────────────────────────

def _get_font(size=14):
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", size)
    except (IOError, OSError):
        try:
            return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
        except (IOError, OSError):
            return ImageFont.load_default()


def _draw_robot(draw, cx, cy, yaw, color=(255, 0, 0), radius=10):
    pts = [
        (cx + radius * math.cos(yaw), cy - radius * math.sin(yaw)),
        (cx + radius * 0.6 * math.cos(yaw + 2.5), cy - radius * 0.6 * math.sin(yaw + 2.5)),
        (cx + radius * 0.6 * math.cos(yaw - 2.5), cy - radius * 0.6 * math.sin(yaw - 2.5)),
    ]
    draw.polygon([(p[0], p[1]) for p in pts], fill=color, outline=(0, 0, 0))


def _draw_laser(draw, robot_x, robot_y, robot_yaw, ranges, angles, color=(0, 200, 0)):
    for r, ang in zip(ranges, angles):
        if r > 7.9:
            continue
        theta = robot_yaw + ang
        ex = robot_x + r * math.cos(theta)
        ey = robot_y + r * math.sin(theta)
        row, col = _world_to_pixel(robot_x, robot_y)
        erow, ecol = _world_to_pixel(ex, ey)
        draw.line([(col, row), (ecol, erow)], fill=color, width=1)


def _draw_goal(draw, gx, gy):
    row, col = _world_to_pixel(gx, gy)
    r = 12
    draw.ellipse([col - r, row - r, col + r, row + r], fill=(0, 200, 0), outline=(0, 0, 0))
    draw.line([col - r - 4, row, col + r + 4, row], fill=(0, 0, 0), width=2)
    draw.line([col, row - r - 4, col, row + r + 4], fill=(0, 0, 0), width=2)


def _draw_trajectory(draw, traj, color=(200, 0, 0)):
    pts = []
    for wp in traj:
        x, y = wp[0], wp[1]
        row, col = _world_to_pixel(x, y)
        pts.append((col, row))
    if len(pts) > 1:
        draw.line(pts, fill=color, width=3)


def _draw_legend(draw, text_lines, font_size=12):
    font = _get_font(font_size)
    line_h = font_size + 6
    box_w = 320
    box_h = len(text_lines) * line_h + 12
    draw.rectangle([5, 5, 5 + box_w, 5 + box_h], fill=(255, 255, 255), outline=(0, 0, 0))
    for i, line in enumerate(text_lines):
        draw.text((12, 10 + i * line_h), line, fill=(0, 0, 0), font=font)


def _draw_info(draw, text, y=5):
    font = _get_font(14)
    draw.text((10, y), text, fill=(50, 50, 50), font=font)


def _draw_cost_overlay(draw, cost_map, alpha=60):
    overlay = Image.new("RGBA", (_map_w, _map_h), (0, 0, 0, 0))
    opix = overlay.load()
    for y in range(_map_h):
        for x in range(_map_w):
            c = cost_map[y][x]
            if c > 20:
                a = min(alpha, int(c * 2.55))
                opix[x, y] = (255, 0, 0, a)
    draw._image.paste(overlay, (0, 0), overlay)


def _draw_particles(draw, particles):
    for px, py, _ in particles:
        row, col = _world_to_pixel(px, py)
        draw.point((col, row), fill=(100, 100, 255))


def _draw_path(draw, path, color=(0, 0, 200)):
    pts = [(_world_to_pixel(x, y)[1], _world_to_pixel(x, y)[0]) for x, y in path]
    if len(pts) > 1:
        draw.line(pts, fill=color, width=4)


# ── rendering functions ────────────────────────────────────────────────────

def render_mapping(frames, fps, out_dir):
    """Progressive map building (Tarea 1)."""
    total = len(frames)
    print(f"  Rendering {total} frames...")
    fd = tempfile.mkdtemp()
    for idx, (rx, ry, ryaw) in enumerate(frames):
        pct = 0.3 + 0.7 * idx / max(1, total - 1)
        rgb = _render_partial_map(pct)
        d = ImageDraw.Draw(rgb)
        _draw_trajectory(d, frames[:idx + 1], color=(180, 60, 60))
        row, col = _world_to_pixel(rx, ry)
        _draw_robot(d, col, row, ryaw)
        rng, ang = _simulate_laser(rx, ry, ryaw)
        _draw_laser(d, rx, ry, ryaw, rng, ang)
        _draw_info(d, f"Progreso: {int(pct*100)}% | Escaneo...")
        _draw_legend(d, ["Tarea 1: Mapeo Gmapping", f"Frame: {idx+1}/{total}",
                         f"Robot: ({rx:.1f}, {ry:.1f})", f"Mapa: {int(pct*100)}%"])
        rgb.save(os.path.join(fd, f"frame_{idx:06d}.png"))
    print(f"  {total} frames OK")
    return fd


def render_localization(frames, fps, out_dir):
    """AMCL localization (Tarea 2)."""
    total = len(frames)
    print(f"  Rendering {total} frames...")
    fd = tempfile.mkdtemp()
    for idx, (rx, ry, ryaw) in enumerate(frames):
        p = idx / max(1, total - 1)
        spread = max(0.2, 2.0 - p * 1.8)
        rgb = _map_rgb_base.copy()
        d = ImageDraw.Draw(rgb)
        _draw_trajectory(d, frames[:idx + 1], color=(60, 60, 180))
        parts = _generate_particles(rx, ry, ryaw, num=80, spread=spread)
        _draw_particles(d, parts)
        rng, ang = _simulate_laser(rx, ry, ryaw)
        _draw_laser(d, rx, ry, ryaw, rng, ang)
        row, col = _world_to_pixel(rx, ry)
        _draw_robot(d, col, row, ryaw)
        _draw_info(d, f"Partículas: 80 | Spread: {spread:.2f}m")
        _draw_legend(d, ["Tarea 2: Localización AMCL", f"Frame: {idx+1}/{total}",
                         f"Robot: ({rx:.1f}, {ry:.1f})", "Verde: LaserScan",
                         "Azul: Partículas AMCL"])
        rgb.save(os.path.join(fd, f"frame_{idx:06d}.png"))
    print(f"  {total} frames OK")
    return fd


def render_navigation(frames, fps, out_dir, goal):
    """Navigation with move_base (Tarea 3)."""
    total = len(frames)
    print(f"  Rendering {total} frames...")
    fd = tempfile.mkdtemp()
    start = (-10.0, -10.0)
    path_wp = _generate_path_wp(start, goal)
    cost = _get_cost_map()
    for idx, (rx, ry, ryaw) in enumerate(frames):
        p = idx / max(1, total - 1)
        rgb = _map_rgb_base.copy()
        d = ImageDraw.Draw(rgb)
        _draw_cost_overlay(d, cost, alpha=int(60 * min(1.0, p / 0.3)))
        _draw_path(d, path_wp)
        _draw_trajectory(d, frames[:idx + 1], color=(180, 60, 60))
        _draw_goal(d, goal[0], goal[1])
        rng, ang = _simulate_laser(rx, ry, ryaw)
        _draw_laser(d, rx, ry, ryaw, rng, ang)
        row, col = _world_to_pixel(rx, ry)
        _draw_robot(d, col, row, ryaw)
        dx, dy = goal[0] - rx, goal[1] - ry
        dist = math.sqrt(dx * dx + dy * dy)
        _draw_info(d, f"Distancia meta: {dist:.1f}m")
        _draw_legend(d, ["Tarea 3: Navegación (move_base)", f"Frame: {idx+1}/{total}",
                         f"Robot: ({rx:.1f}, {ry:.1f})",
                         f"Meta: ({goal[0]:.1f}, {goal[1]:.1f})",
                         f"Distancia: {dist:.1f}m",
                         "Rojo: Costmap | Azul: Ruta A*"])
        rgb.save(os.path.join(fd, f"frame_{idx:06d}.png"))
    print(f"  {total} frames OK")
    return fd


# ── video assembly ─────────────────────────────────────────────────────────

def _frames_to_video(frame_dir, out_path, name):
    out = os.path.join(out_path, name)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    # Try ffmpeg via PATH (may be ~/.local/bin)
    for cmd_name in ["ffmpeg", os.path.expanduser("~/.local/bin/ffmpeg")]:
        if os.path.exists(cmd_name) or (cmd_name == "ffmpeg" and subprocess.run(["which", "ffmpeg"], capture_output=True).returncode == 0):
            break
    else:
        cmd_name = "ffmpeg"
    try:
        subprocess.run([
            cmd_name, "-y", "-framerate", "10", "-pattern_type", "glob",
            "-i", f"{frame_dir}/frame_*.png",
            "-c:v", "libx264", "-pix_fmt", "yuv420p",
            "-preset", "medium", "-crf", "23", "-movflags", "+faststart", out
        ], capture_output=True, timeout=120, check=True)
        print(f"  ✅ {name} (H.264)")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        # Fallback to MPEG4
        try:
            subprocess.run([
                cmd_name, "-y", "-framerate", "10", "-pattern_type", "glob",
                "-i", f"{frame_dir}/frame_*.png",
                "-c:v", "mpeg4", "-pix_fmt", "yuv420p", "-q:v", "3", out
            ], capture_output=True, timeout=120, check=True)
            print(f"  ✅ {name} (MPEG4)")
            return True
        except Exception as e:
            print(f"  ❌ ffmpeg: {e}")
            print(f"  ⚠ Frames: {frame_dir}")
            return False


# ── main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Render simulation videos from PGM map")
    parser.add_argument("--type", required=True, choices=["mapping", "localization", "navigation"])
    parser.add_argument("--output", default="videos")
    parser.add_argument("--duration", type=int, default=20)
    parser.add_argument("--fps", type=int, default=10)
    parser.add_argument("--goal-x", type=float, default=5.0)
    parser.add_argument("--goal-y", type=float, default=3.0)
    args = parser.parse_args()

    total = args.duration * args.fps
    _load_map()
    print(f"\n  Mapa: {_map_w}x{_map_h}, res={_map_resolution}, "
          f"origin=({_map_origin[0]:.2f}, {_map_origin[1]:.2f})")
    print(f"  Tipo: {args.type}, Duración: {args.duration}s, FPS: {args.fps}, Frames: {total}\n")

    if args.type == "mapping":
        poses = _generate_poses_t1(total)
        fd = render_mapping(poses, args.fps, args.output)
        out_name = "tarea1_mapping.mp4"
    elif args.type == "localization":
        poses = _generate_poses_t2(total)
        fd = render_localization(poses, args.fps, args.output)
        out_name = "tarea2_localization.mp4"
    else:
        poses = _generate_poses_t3(total, (args.goal_x, args.goal_y))
        fd = render_navigation(poses, args.fps, args.output, (args.goal_x, args.goal_y))
        out_name = "tarea3_navigation.mp4"

    _frames_to_video(fd, args.output, out_name)
    shutil.rmtree(fd, ignore_errors=True)


if __name__ == "__main__":
    main()
