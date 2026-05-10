#!/usr/bin/env python3
"""Capture ROS topics to JSON files. Designed to run inside container via docker exec.
Usage: python3 capture_topics.py --duration 30 --outdir /ros_ws/captures
"""
import argparse
import json
import os
import signal
import sys
import time
from collections import defaultdict

# Ensure geometry_msgs is importable (rosmsg dependency)
try:
    import rospy
except ImportError:
    print("ERROR: rospy not available. Run inside ROS container: source /opt/ros/noetic/setup.bash")
    sys.exit(1)

TOPICS = [
    "/scan",
    "/amcl_pose",
    "/differential_robot/odom",
    "/cmd_vel",
    "/move_base/current_goal",
    "/move_base_simple/goal",
    "/particlecloud",
]


def _ros_msg_to_dict(msg):
    """Recursively convert ROS message to JSON-serializable dict."""
    import genpy
    if isinstance(msg, genpy.Message):
        d = {}
        for slot in msg.__slots__:
            val = getattr(msg, slot, None)
            if isinstance(val, genpy.Message):
                d[slot] = _ros_msg_to_dict(val)
            elif isinstance(val, tuple):
                d[slot] = [_ros_msg_to_dict(v) if isinstance(v, genpy.Message) else v for v in val]
            elif hasattr(val, '__iter__') and not isinstance(val, str):
                d[slot] = list(val)
            else:
                d[slot] = val
        return d
    return str(msg)


# Shared buffer
data = defaultdict(list)
running = True


def make_cb(topic):
    def cb(msg):
        stamp = time.time()
        if hasattr(msg, 'header') and hasattr(msg.header, 'stamp'):
            try:
                stamp = msg.header.stamp.to_sec()
            except Exception:
                pass
        d = _ros_msg_to_dict(msg)
        data[topic].append({"stamp": stamp, "msg": d})
    return cb


def signal_handler(sig, frame):
    global running
    print("\nStopping capture...")
    running = False


def main():
    global running
    parser = argparse.ArgumentParser(description="Capture ROS topics to JSON")
    parser.add_argument("--duration", type=float, default=15.0,
                        help="Capture duration in seconds")
    parser.add_argument("--outdir", default="/ros_ws/captures",
                        help="Output directory for JSON files")
    args = parser.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    rospy.init_node("topic_capture", anonymous=True, disable_signals=True)

    # Subscribe to all topics
    subs = []
    for topic in TOPICS:
        try:
            # Determine message type from topic
            topic_class, topic_name, _ = rospy.get_topic_class(topic)
            if topic_class is None:
                print(f"  ⚠️  Cannot determine type for {topic}, skipping")
                continue
            sub = rospy.Subscriber(topic, topic_class, make_cb(topic))
            subs.append(sub)
            print(f"  Subscribed to {topic} ({topic_class.__name__})")
        except Exception as e:
            print(f"  ⚠️  Error subscribing to {topic}: {e}")

    print(f"\nCapturing for {args.duration}s...")
    start = time.time()
    rate = rospy.Rate(20)
    while running and (time.time() - start) < args.duration:
        rate.sleep()

    print("\nSaving captures...")
    for topic, msgs in data.items():
        safe_name = topic.replace("/", "_").strip("_")
        fpath = os.path.join(args.outdir, f"{safe_name}.json")
        with open(fpath, "w") as f:
            json.dump(msgs, f)
        print(f"  {topic}: {len(msgs)} msgs -> {fpath}")

    print(f"Done. Files in {args.outdir}/")
    print(json.dumps({k: len(v) for k, v in data.items()}))


if __name__ == "__main__":
    main()
