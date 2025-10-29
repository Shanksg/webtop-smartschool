#!/usr/bin/env python3
"""
Quick test script to run a single homework check
This bypasses the scheduler and runs one check immediately
"""

from smartschool_monitor_v2 import SmartSchoolMonitor
from loguru import logger

if __name__ == "__main__":
    logger.info("Running single homework check...")

    monitor = SmartSchoolMonitor()

    # Run one check immediately
    monitor.run_all_checks()

    logger.info("Test complete! Check the output above.")
