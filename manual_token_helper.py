#!/usr/bin/env python3
"""
Manual Token Helper - No Selenium Required!
Just copy/paste your token from the browser
"""

import json
import yaml
from pathlib import Path
from datetime import datetime

def save_manual_token():
    """Save manually extracted token"""

    print("=" * 60)
    print("SmartSchool Manual Token Helper")
    print("=" * 60)
    print()
    print("HOW TO GET YOUR TOKEN:")
    print("1. Open Chrome and go to https://webtop.smartschool.co.il")
    print("2. Login normally (solve the captcha)")
    print("3. Press F12 to open Developer Tools")
    print("4. Go to 'Application' tab")
    print("5. In the left sidebar, click 'Cookies' → 'https://webtop.smartschool.co.il'")
    print("6. Find 'webToken' and copy its VALUE")
    print()
    print("=" * 60)

    token = input("\nPaste your webToken here: ").strip()

    if not token:
        print("✗ No token provided!")
        return False

    print(f"\n✓ Token received (length: {len(token)})")

    # Load config to get username
    config_path = Path("config/config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    student = config['students'][0]
    username = student['username']
    student_params = student.get('student_params')

    # Save token cache
    cache_file = Path("config/token_cache.json")
    cache = {}

    if cache_file.exists():
        with open(cache_file, 'r') as f:
            cache = json.load(f)

    cache[username] = {
        'token': token,
        'student_params': student_params,
        'timestamp': datetime.now().isoformat()
    }

    cache_file.parent.mkdir(exist_ok=True, parents=True)
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)

    print(f"\n✓ Token saved to {cache_file}")
    print(f"✓ This token will be valid for about 24 hours")
    print()
    print("Now you can run: python smartschool_monitor_v2.py")
    print("It will use this cached token without opening a browser!")
    print("=" * 60)

    return True

if __name__ == "__main__":
    save_manual_token()
