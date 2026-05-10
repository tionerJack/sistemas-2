#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
# record_topic_data.sh
# Captura tópicos ROS desde el contenedor ros_noetic_sim usando
# capture_topics.py (suscriptor Python, sin dependencia de /clock).
# Uso: bash record_topic_data.sh [duración_segundos] [nombre_captura]
# Ejemplo: bash record_topic_data.sh 45 tarea1_mapping
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

CONTAINER="ros_noetic_sim"
DURATION="${1:-30}"
CAPTURE_NAME="${2:-simulation_data}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
HOST_OUT_DIR="$SCRIPT_DIR/captures"
CONTAINER_OUT_DIR="/ros_ws/captures"

mkdir -p "$HOST_OUT_DIR"

echo "=== record_topic_data.sh ==="
echo "Container: $CONTAINER"
echo "Duration: ${DURATION}s"
echo "Capture name: ${CAPTURE_NAME}"
echo ""

# ── 1. Copy capture script to container ─────────────────────────────────────
echo "[1/3] Deploying capture_topics.py to container..."
sudo docker cp "$SCRIPT_DIR/capture_topics.py" "${CONTAINER}:/tmp/capture_topics.py"

# ── 2. Run capture inside container ─────────────────────────────────────────
echo "[2/3] Starting topic capture (${DURATION}s)..."
sudo docker exec "$CONTAINER" bash -c "
    source /opt/ros/noetic/setup.bash &&
    source /ros_ws/devel/setup.bash 2>/dev/null || true &&
    export ROS_MASTER_URI=http://localhost:11311 &&
    export ROS_HOSTNAME=localhost &&
    mkdir -p ${CONTAINER_OUT_DIR}/${CAPTURE_NAME} &&
    python3 /tmp/capture_topics.py \
        --duration ${DURATION} \
        --outdir ${CONTAINER_OUT_DIR}/${CAPTURE_NAME}
" 2>&1

echo ""
echo "[3/3] Copying captures to host..."

# Clean host dir for this capture
mkdir -p "$HOST_OUT_DIR/$CAPTURE_NAME"

# Copy each JSON file
sudo docker cp "${CONTAINER}:${CONTAINER_OUT_DIR}/${CAPTURE_NAME}/." "$HOST_OUT_DIR/$CAPTURE_NAME/" 2>/dev/null || {
    echo "⚠️  No JSON files found in container output."
    echo "Checking container output dir:"
    sudo docker exec "$CONTAINER" ls -la "${CONTAINER_OUT_DIR}/${CAPTURE_NAME}/" 2>/dev/null || echo "  (empty)"
    exit 1
}

echo ""
echo "Captured files in $HOST_OUT_DIR/$CAPTURE_NAME/:"
ls -lh "$HOST_OUT_DIR/$CAPTURE_NAME/" | head -20
echo ""

# Show message counts
echo "=== Message counts ==="
for f in "$HOST_OUT_DIR/$CAPTURE_NAME"/*.json; do
    if [ -f "$f" ]; then
        count=$(python3 -c "import json; d=json.load(open('$f')); print(len(d))" 2>/dev/null || echo "?")
        echo "  $(basename "$f"): $count msgs"
    fi
done

echo ""
echo "✅ Capture saved to: $HOST_OUT_DIR/$CAPTURE_NAME/"
