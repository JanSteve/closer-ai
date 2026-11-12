#!/usr/bin/env python3
"""
scripts/run_batch_generator.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Programmatic Video Generation Script entry point for CLOSER AI.
Invokes closer.video.batch_generator with command-line arguments.
"""

import sys
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from closer.video.batch_generator import main

if __name__ == "__main__":
    main()
