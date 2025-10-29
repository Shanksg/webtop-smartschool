#!/usr/bin/env python3
"""
Test script to simulate detecting NEW homework
This clears the state so the next run will detect all homework as "new"
NOTE: Only homework for TODAY will trigger notifications
"""

import json
from pathlib import Path
from datetime import datetime
from loguru import logger
from smartschool_monitor_v2 import SmartSchoolMonitor

if __name__ == "__main__":
    print("="*70)
    print("Testing NEW Homework Detection")
    print("="*70)
    print(f"Today's date: {datetime.now().strftime('%Y-%m-%d')}")
    print("NOTE: Only homework for TODAY will trigger notifications")
    print("="*70)

    # Initialize monitor
    monitor = SmartSchoolMonitor()

    print("\n1. Clearing homework state to simulate fresh start...")
    monitor.homework_state = {}
    monitor.save_state()
    logger.info("State cleared - all homework will be detected as NEW")

    print("\n2. Running homework check...")
    monitor.run_all_checks()

    print("\n3. Checking results...")
    state_file = Path("config/homework_state.json")
    if state_file.exists():
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)

        for student, homework_dict in state.items():
            print(f"\n📚 {student}: {len(homework_dict)} homework items detected\n")

            # Group homework by date
            by_date = {}
            for hw_hash, hw_data in homework_dict.items():
                item = hw_data['item']
                date = item['date'][:10]  # Just the date part
                if date not in by_date:
                    by_date[date] = []
                by_date[date].append(item)

            # Display homework organized by date
            today = datetime.now().strftime('%Y-%m-%d')
            for date in sorted(by_date.keys()):
                is_today = (date == today)
                date_label = f"📅 {date}" + (" ⭐ TODAY - WILL NOTIFY" if is_today else " (not today, no notification)")
                print(f"   {date_label}")
                for idx, item in enumerate(by_date[date], 1):
                    subject = item.get('subject', 'Unknown')
                    teacher = item.get('teacher', 'Unknown')
                    homework = item.get('homework', '')

                    print(f"      {idx}. {subject} - {teacher}")

                    # Print homework with nice wrapping (max 70 chars per line)
                    hw_lines = homework.split('\n')
                    for line in hw_lines[:3]:  # Show first 3 lines
                        if len(line) > 70:
                            print(f"         {line[:70]}...")
                        else:
                            print(f"         {line}")

                    if len(hw_lines) > 3:
                        print(f"         ... ({len(hw_lines) - 3} more lines)")
                    print()

    print("="*70)
    print("Test Complete!")
    print("="*70)
    print("\n📬 Notification Status:")
    print("   Check your Home Assistant for the notification!")
    print("\nNext steps:")
    print("1. Run this script again - you should see 'No new homework' (already tracked)")
    print("2. Check logs/smartschool-monitor.log for detailed output")
    print("3. Run 'python test_monitor.py' to check without clearing state")
