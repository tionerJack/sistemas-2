#!/usr/bin/env python3
"""Wrapper: render mapping video (progressive map building).

Usage:
  python3 render_map_video.py [--duration 20] [--fps 10] [--output dir]
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render_video import main
main()
