#!/usr/bin/env python3
"""
Simple browser-based login - Just login manually, we'll extract the token
Much more reliable than trying to automate the Angular SPA
"""

import time
import json
import undetected_chromedriver as uc
from datetime import datetime
import yaml
from pathlib import Path

def browser_login():
    """Open browser and wait for manual login"""

    print("=" * 60)
    print("SmartSchool Browser Login Helper")
    print("=" * 60)
    print()
    print("INSTRUCTIONS:")
    print("1. A Chrome window will open")
    print("2. Login to SmartSchool MANUALLY (solve captcha, etc.)")
    print("3. Wait until you see your homepage")
    print("4. Come back here and press ENTER")
    print()
    print("=" * 60)
    print()

    # Setup Chrome
    print("Opening Chrome browser...")
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    driver = uc.Chrome(options=options, use_subprocess=True)

    # Navigate to login page
    login_url = "https://webtop.smartschool.co.il/account/login"
    driver.get(login_url)
    print(f"✓ Navigated to: {login_url}")

    # Wait for page to load
    time.sleep(5)

    # Try to dismiss cookie banner if it exists
    print("Checking for cookie consent banner...")
    try:
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC

        # Common selectors for close buttons, accept buttons, or dismiss overlays
        cookie_selectors = [
            "button.close",
            "button.dismiss",
            "a.close",
            ".cookie-close",
            "button[aria-label='Close']",
            "button[aria-label='סגור']",  # Hebrew for Close
            ".modal-close",
            "[class*='close']",
            "//button[contains(text(), 'X')]",
            "//button[contains(text(), 'סגור')]",  # Hebrew for Close
            "//a[contains(text(), 'X')]",
        ]

        cookie_handled = False
        for selector in cookie_selectors:
            try:
                if selector.startswith('//'):
                    # XPath selector
                    element = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                else:
                    # CSS selector
                    element = WebDriverWait(driver, 2).until(
                        EC.element_to_be_clickable((By.CSS_SELECTOR, selector))
                    )
                element.click()
                print(f"✓ Dismissed cookie banner")
                cookie_handled = True
                time.sleep(1)
                break
            except:
                continue

        if not cookie_handled:
            print("ℹ No cookie banner found (or it auto-dismisses)")
            print("  The banner usually disappears automatically - continue with login")

    except Exception as e:
        print(f"ℹ Cookie banner check complete (continuing anyway)")

    time.sleep(2)

    print()
    print("👉 NOW LOGIN IN THE BROWSER WINDOW!")
    print("   (Solve captcha, enter credentials, etc.)")
    print()

    # Wait for user to login
    input("Press ENTER after you've successfully logged in... ")

    # Extract token from cookies
    print("\nExtracting token from cookies...")
    cookies = driver.get_cookies()

    web_token = None
    for cookie in cookies:
        if cookie['name'] == 'webToken':
            web_token = cookie['value']
            break

    if not web_token:
        print("✗ Could not find webToken cookie!")
        print("   Make sure you're logged in and on the homepage")
        driver.quit()
        return False

    print(f"✓ Found webToken: {web_token[:50]}...")

    # Load config to get student info
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
        'token': web_token,
        'student_params': student_params,
        'timestamp': datetime.now().isoformat()
    }

    cache_file.parent.mkdir(exist_ok=True, parents=True)
    with open(cache_file, 'w') as f:
        json.dump(cache, f, indent=2)

    print(f"\n✓ Token saved to {cache_file}")
    print(f"✓ Token will be valid for about 24 hours")
    print()
    print("=" * 60)
    print("SUCCESS! You can now run:")
    print("  python smartschool_monitor_v2.py")
    print()
    print("The monitor will use this cached token automatically!")
    print("=" * 60)

    # Keep browser open for a bit
    print("\nClosing browser in 5 seconds...")
    time.sleep(5)
    driver.quit()

    return True

if __name__ == "__main__":
    try:
        browser_login()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
