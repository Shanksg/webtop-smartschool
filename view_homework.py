#!/usr/bin/env python3
"""
View currently tracked homework in a nice format
"""

import json
from pathlib import Path
from datetime import datetime

def view_homework():
    state_file = Path("config/homework_state.json")

    if not state_file.exists():
        print("❌ No homework state file found. Run the monitor first!")
        return

    with open(state_file, 'r', encoding='utf-8') as f:
        state = json.load(f)

    print("\n" + "="*70)
    print("📚 CURRENT HOMEWORK TRACKER")
    print("="*70)

    for student, homework_dict in state.items():
        print(f"\n👤 Student: {student}")
        print(f"   Total homework items: {len(homework_dict)}")
        print()

        # Group by date
        by_date = {}
        for hw_hash, hw_data in homework_dict.items():
            item = hw_data['item']
            date = item['date'][:10]  # Just the date part
            if date not in by_date:
                by_date[date] = []
            by_date[date].append(item)

        # Display by date
        for date in sorted(by_date.keys()):
            print(f"   📅 {date}")
            for item in by_date[date]:
                print(f"      • {item['subject']} ({item['teacher']})")
                homework = item['homework']
                if len(homework) > 80:
                    homework = homework[:80] + "..."
                print(f"        {homework}")
            print()

    print("="*70)

    # Show token status
    token_file = Path("config/token_cache.json")
    if token_file.exists():
        with open(token_file, 'r') as f:
            cache = json.load(f)

        print("\n🔑 TOKEN STATUS")
        for username, data in cache.items():
            timestamp = datetime.fromisoformat(data['timestamp'])
            age_hours = (datetime.now() - timestamp).total_seconds() / 3600
            remaining_hours = 23 - age_hours

            if remaining_hours > 0:
                print(f"   ✅ Token valid for {remaining_hours:.1f} more hours")
            else:
                print(f"   ⚠️  Token expired! Run: python manual_token_extractor.py")

    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    view_homework()
