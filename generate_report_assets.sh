#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# generate_report_assets.sh
# Generates all visual assets for the ROS Noetic simulation report (headless).
# Usage: bash generate_report_assets.sh
# Output: ros_ws/warehouse_map.png, ros_ws/annotated_map.png, ros_ws/ros_pipeline_diagram.png
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
OUT_DIR="$SCRIPT_DIR/ros_ws"
MAP_PGM="$OUT_DIR/maps/warehouse_map.pgm"
MAP_YAML="$OUT_DIR/maps/warehouse_map.yaml"
GENERATOR="$OUT_DIR/generate_assets.py"

echo "=== generate_report_assets.sh ==="
echo "Output dir: $OUT_DIR"

# ── Check prerequisites ──────────────────────────────────────────────────────

if ! command -v python3 &>/dev/null; then
    echo "ERROR: python3 not found. Install Python 3."
    exit 1
fi

if ! python3 -c "from PIL import Image; print('Pillow OK')" 2>/dev/null; then
    echo "Pillow not found. Trying to install..."
    if command -v pip3 &>/dev/null; then
        pip3 install --user Pillow 2>&1 || pip3 install Pillow 2>&1
    else
        echo "ERROR: pip3 not available. Use system package manager:"
        echo "  sudo apt install python3-pil  # Debian/Ubuntu"
        exit 1
    fi
fi

if ! command -v dot &>/dev/null; then
    echo "ERROR: Graphviz (dot) not found. Install it:"
    echo "  sudo apt install graphviz  # Debian/Ubuntu"
    exit 1
fi

# ── Check input files ────────────────────────────────────────────────────────

for f in "$MAP_PGM" "$MAP_YAML"; do
    if [ ! -f "$f" ]; then
        echo "ERROR: Missing $f"
        exit 1
    fi
done
echo "Input files: OK"

# ── Generate assets ──────────────────────────────────────────────────────────

if [ -f "$GENERATOR" ]; then
    echo "Using Python generator script..."
    python3 "$GENERATOR"
else
    echo "Generator script not found, using standalone commands..."
    # Fallback: PGM → PNG via ImageMagick
    convert "$MAP_PGM" -negate "$OUT_DIR/warehouse_map.png"
    echo "✅ warehouse_map.png (ImageMagick)"
    # Annotated map via ImageMagick with simple coordinate overlay
    convert "$MAP_PGM" -negate \
        -fill red -draw "circle 288,288 292,292" \
        -fill red -draw "text 298,278 'Origen (0,0)'" \
        -fill red -draw "line 288,288 488,288" \
        -fill green -draw "line 288,288 288,88" \
        "$OUT_DIR/annotated_map.png"
    echo "✅ annotated_map.png (ImageMagick fallback)"
    # Pipeline diagram via Graphviz
    dot -Tpng -o "$OUT_DIR/ros_pipeline_diagram.png" /dev/null 2>/dev/null || \
        echo "⚠️  ros_pipeline_diagram.png requires the DOT source"
fi

# ── Verify outputs ───────────────────────────────────────────────────────────

echo ""
echo "=== Verification ==="
for f in warehouse_map.png annotated_map.png ros_pipeline_diagram.png; do
    path="$OUT_DIR/$f"
    if [ -f "$path" ]; then
        size=$(stat --printf="%s" "$path" 2>/dev/null || stat -f%z "$path" 2>/dev/null)
        echo "✅ $f  ($(( size / 1024 )) KB)"
    else
        echo "❌ $f  NOT FOUND"
    fi
done

echo ""
echo "=== Done ==="
echo "Assets saved to: $OUT_DIR"
