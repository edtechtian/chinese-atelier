#!/usr/bin/env python3
"""Compatibility entry point for the current, complete adaptation pipeline.

The earlier three-question generator is retired. By default this integrates the
existing editorial specification. Use --author only after backing up teacher edits.
"""
from pathlib import Path
import runpy
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

if __name__ == '__main__':
    runpy.run_path(str(ROOT / 'scripts/build_adaptations.py'), run_name='__main__')
