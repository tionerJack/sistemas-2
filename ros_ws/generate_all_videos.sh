#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# generate_all_videos.sh
# Orquestador: renderiza 3 videos de simulación desde el mapa generado.
# Uso: bash generate_all_videos.sh [--duration 30] [--fps 10]
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="$SCRIPT_DIR/videos"
DURATION=20
FPS=10

while [[ $# -gt 0 ]]; do
    case "$1" in
        --duration) DURATION="$2"; shift 2 ;;
        --fps) FPS="$2"; shift 2 ;;
        *) echo "Unknown: $1"; exit 1 ;;
    esac
done

echo "╔════════════════════════════════════════════════════════╗"
echo "║      generate_all_videos.sh — Generador de Videos     ║"
echo "╚════════════════════════════════════════════════════════╝"
echo "Duration: ${DURATION}s | FPS: ${FPS}"
echo "Output:   $OUT_DIR"
echo ""

mkdir -p "$OUT_DIR"

# ── 0. Verify prerequisites ────────────────────────────────────────────────
echo "=== [0/4] Verificando prerequisitos ==="

if ! command -v ffmpeg &>/dev/null; then
    echo "  ffmpeg no encontrado. Instalando..."
    sudo apt-get update -qq && sudo apt-get install -y -qq ffmpeg 2>/dev/null || true
fi
echo "  ffmpeg: $(ffmpeg -version 2>&1 | head -1 || echo 'no disponible')"

python3 -c "from PIL import Image; print('  Pillow OK')" 2>/dev/null || {
    echo "  Pillow no encontrado. Instalando..."
    pip3 install --user Pillow 2>/dev/null || sudo apt-get install -y -qq python3-pil 2>/dev/null
}

if [ ! -f "$SCRIPT_DIR/maps/warehouse_map.pgm" ]; then
    echo "  ❌ Mapa no encontrado en $SCRIPT_DIR/maps/"
    echo "  Copia el mapa del contenedor:"
    echo "    sudo docker cp ros_noetic_sim:/ros_ws/maps/warehouse_map.pgm \"$SCRIPT_DIR/maps/\""
    echo "    sudo docker cp ros_noetic_sim:/ros_ws/maps/warehouse_map.yaml \"$SCRIPT_DIR/maps/\""
    exit 1
fi
echo "  Mapa: warehouse_map.pgm ✓"
echo ""

# ── 1. Render Mapping ──────────────────────────────────────────────────────
echo "=== [1/4] Tarea 1: Mapping ==="
python3 "$SCRIPT_DIR/render_video.py" \
    --type mapping --duration "$DURATION" --fps "$FPS" --output "$OUT_DIR" 2>&1
echo ""

# ── 2. Render Localization ─────────────────────────────────────────────────
echo "=== [2/4] Tarea 2: Localization ==="
python3 "$SCRIPT_DIR/render_video.py" \
    --type localization --duration "$DURATION" --fps "$FPS" --output "$OUT_DIR" 2>&1
echo ""

# ── 3. Render Navigation ───────────────────────────────────────────────────
echo "=== [3/4] Tarea 3: Navigation ==="
python3 "$SCRIPT_DIR/render_video.py" \
    --type navigation --duration "$DURATION" --fps "$FPS" \
    --goal-x 5.0 --goal-y 3.0 --output "$OUT_DIR" 2>&1
echo ""

# ── 4. Verify ──────────────────────────────────────────────────────────────
echo "=== [4/4] Verificando videos ==="
echo ""
echo "╔════════════════════════════════════════════════════════╗"
echo "║                 RESULTADOS FINALES                    ║"
echo "╚════════════════════════════════════════════════════════╝"

for video in tarea1_mapping.mp4 tarea2_localization.mp4 tarea3_navigation.mp4; do
    path="$OUT_DIR/$video"
    if [ -f "$path" ]; then
        size=$(du -h "$path" | cut -f1)
        dur=$(ffprobe -v error -show_entries format=duration \
              -of default=noprint_wrappers=1:nokey=1 "$path" 2>/dev/null || echo "?")
        echo "  ✅ $video  (${size}, ${dur}s)"
    else
        echo "  ❌ $video  NO ENCONTRADO"
    fi
done
echo ""
echo "Videos: $OUT_DIR/"
