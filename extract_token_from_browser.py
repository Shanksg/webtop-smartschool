#!/usr/bin/env python3
"""
Extract webToken from your existing Chrome browser session
No need to open new windows or automate anything!
"""

import json
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import yaml
import os
import platform

def find_chrome_cookies():
    """Find Chrome cookies database based on OS"""
    system = platform.system()

    if system == "Darwin":  # macOS
        cookies_path = Path.home() / "Library/Application Support/Google/Chrome/Default/Cookies"
    elif system == "Linux":
        cookies_path = Path.home() / ".config/google-chrome/Default/Cookies"
    elif system == "Windows":
        cookies_path = Path.home() / "AppData/Local/Google/Chrome/User Data/Default/Cookies"
    else:
        return None

    return cookies_path if cookies_path.exists() else None

def extract_token_from_chrome():
    """Extract webToken from Chrome cookies"""

    print("=" * 60)
    print("Extract Token from Your Existing Chrome Session")
    print("=" * 60)
    print()

    # Find Chrome cookies
    cookies_path = find_chrome_cookies()

    if not cookies_path:
        print("✗ Could not find Chrome cookies database")
        print("   Make sure Chrome is installed")
        return False

    print(f"✓ Found Chrome cookies: {cookies_path}")
    print()
    print("IMPORTANT:")
    print("1. Make sure you're logged into SmartSchool in Chrome")
    print("2. Close ALL Chrome windows (cookies DB is locked when Chrome is open)")
    print("3. Then come back here and press ENTER")
    print()
    input("Press ENTER when Chrome is closed... ")

    # Copy cookies to temp location (can't read while locked)
    temp_cookies = Path("/tmp/chrome_cookies_temp.db")

    try:
        shutil.copy2(cookies_path, temp_cookies)
        print("✓ Copied cookies database")
    except Exception as e:
        print(f"✗ Failed to copy cookies: {e}")
        print("   Make sure Chrome is completely closed!")
        return False

    # Read cookies from database
    try:
        conn = sqlite3.connect(temp_cookies)
        cursor = conn.cursor()

        # Query for webToken cookie
        cursor.execute("""
            SELECT name, value, host_key
            FROM cookies
            WHERE host_key LIKE '%smartschool.co.il%'
            AND name = 'webToken'
        """)

        result = cursor.fetchone()
        conn.close()

        # Clean up temp file
        temp_cookies.unlink()

        if not result:
            print("✗ webToken not found in Chrome cookies")
            print("   Make sure you're logged into SmartSchool in Chrome")
            print("   Go to https://webtop.smartschool.co.il and login first")
            return False

        cookie_name, cookie_value, host = result
        print(f"✓ Found webToken cookie from {host}")
        print(f"  Token: {cookie_value[:50]}...")

        # Load config
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
            'token': cookie_value,
            'student_params': student_params,
            'timestamp': datetime.now().isoformat()
        }

        cache_file.parent.mkdir(exist_ok=True, parents=True)
        with open(cache_file, 'w') as f:
            json.dump(cache, f, indent=2)

        print()
        print("=" * 60)
        print("✓ SUCCESS! Token extracted and saved")
        print(f"✓ Saved to: {cache_file}")
        print(f"✓ Valid for ~24 hours")
        print()
        print("You can now run:")
        print("  python smartschool_monitor_v2.py")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"✗ Error reading cookies: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    try:
        extract_token_from_chrome()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
