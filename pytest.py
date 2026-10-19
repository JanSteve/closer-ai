#!/usr/bin/env python3
"""
Pytest compatibility CLI runner for CLOSER AI.
Discovers and executes tests in standard verbose pytest formatting.
"""

import sys
import unittest
import time
from pathlib import Path

# Add src to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))

def main():
    print("=" * 70)
    print("                      CLOSER AI TEST RUNNER (pytest)")
    print("=" * 70)
    
    loader = unittest.TestLoader()
    suite = loader.discover("tests", pattern="test_*.py")
    
    runner = unittest.TextTestRunner(verbosity=2)
    start_time = time.time()
    result = runner.run(suite)
    duration = time.time() - start_time
    
    passed = result.testsRun - len(result.failures) - len(result.errors)
    print("=" * 70)
    if result.wasSuccessful():
        print(f"\033[32;1m====== {passed} passed in {duration:.2f}s ======\033[0m")
        sys.exit(0)
    else:
        print(f"\033[31;1m====== {len(result.failures)} failed, {len(result.errors)} errors, {passed} passed in {duration:.2f}s ======\033[0m")
        sys.exit(1)

if __name__ == "__main__":
    main()
