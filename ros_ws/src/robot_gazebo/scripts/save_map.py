#!/usr/bin/env python3
"""Save map from /map topic to PGM/YAML files (works with simulated time)."""
import rospy
import os
import sys
from nav_msgs.msg import OccupancyGrid

MAP_TOPIC = '/map'
DEFAULT_PATH = '/ros_ws/maps/warehouse_map'

def save_map(msg, filepath):
    """Save OccupancyGrid as PGM + YAML."""
    rospy.loginfo(f"Saving map to {filepath} (size: {msg.info.width}x{msg.info.height})")

    # Convert -1 (unknown) to 255 for PGM
    pgm_data = bytearray()
    for cell in msg.data:
        if cell == -1:
            pgm_data.append(205)  # grey for unknown
        elif cell == 0:
            pgm_data.append(254)  # white for free
        elif cell == 100:
            pgm_data.append(0)    # black for occupied
        else:
            pgm_data.append(int(cell * 254 / 100))

    # Write PGM file
    pgm_path = filepath + '.pgm'
    with open(pgm_path, 'wb') as f:
        f.write(b'P5\n')
        f.write(f'{msg.info.width} {msg.info.height}\n'.encode())
        f.write(b'255\n')
        f.write(bytes(pgm_data))
    rospy.loginfo(f"Wrote {pgm_path} ({len(pgm_data)} bytes)")

    # Write YAML file
    origin = msg.info.origin.position
    yaml_path = filepath + '.yaml'
    yaml_content = f"""image: {os.path.basename(pgm_path)}
resolution: {msg.info.resolution}
origin: [{origin.x}, {origin.y}, 0.0]
negate: 0
occupied_thresh: 0.65
free_thresh: 0.196
"""
    with open(yaml_path, 'w') as f:
        f.write(yaml_content)
    rospy.loginfo(f"Wrote {yaml_path}")

    rospy.loginfo(f"Map saved successfully!")
    # Shutdown after saving
    rospy.signal_shutdown("Map saved")

def main():
    rospy.init_node('map_saver_custom', anonymous=True)

    filepath = rospy.get_param('~file', DEFAULT_PATH)
    timeout = rospy.get_param('~timeout', 30.0)

    rospy.loginfo(f"Waiting for map on {MAP_TOPIC} (timeout: {timeout}s)...")
    rospy.loginfo(f"Output: {filepath}.*")

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Subscribe and wait for one message
    msg = rospy.wait_for_message(MAP_TOPIC, OccupancyGrid, timeout=timeout)
    save_map(msg, filepath)

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSException as e:
        rospy.logerr(f"Failed to get map: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        pass
