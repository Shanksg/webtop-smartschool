#!/usr/bin/env python3
"""
Automated login with JavaScript injection to bypass cookie banners
"""

import time
import json
import undetected_chromedriver as uc
from datetime import datetime
import yaml
from pathlib import Path
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def auto_login():
    """Automated login with cookie banner handling via JavaScript"""

    print("=" * 60)
    print("SmartSchool Automated Token Extractor")
    print("=" * 60)

    # Load config
    config_path = Path("config/config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    student = config['students'][0]
    username = student['username']
    password = student['password']
    student_params = student.get('student_params')

    print(f"Username: {username}")
    print("=" * 60)

    # Setup Chrome
    print("\n1. Opening Chrome browser...")
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--start-maximized')

    driver = uc.Chrome(options=options, use_subprocess=True)

    try:
        # Navigate to login page
        login_url = "https://webtop.smartschool.co.il/account/login"
        driver.get(login_url)
        print(f"✓ Navigated to login page")

        # Wait for page to load
        print("\n2. Waiting for page to load...")
        time.sleep(8)  # Give Angular time to initialize

        # Remove any overlays/modals/cookie banners with JavaScript
        print("\n3. Removing cookie banners and overlays...")
        js_remove_overlays = """
        // Remove cookie banners and overlays
        var styles = document.createElement('style');
        styles.innerHTML = `
            .modal-backdrop, .cookie-banner, .cookie-notice, [class*="cookie"],
            [id*="cookie"], .overlay, .popup, [role="dialog"] {
                display: none !important;
            }
            body {
                overflow: auto !important;
            }
        `;
        document.head.appendChild(styles);

        // Remove specific elements
        document.querySelectorAll('.modal-backdrop, .cookie-banner, [class*="cookie"]').forEach(el => {
            el.remove();
        });

        // Enable body scrolling
        document.body.style.overflow = 'auto';
        document.body.style.position = 'relative';

        console.log('Overlays removed');
        """
        driver.execute_script(js_remove_overlays)
        print("✓ Removed overlays with JavaScript")
        time.sleep(2)

        # Find username field using multiple strategies
        print("\n4. Finding login fields...")
        username_field = None

        # Try different selectors for Angular apps
        selectors = [
            "input[type='text']",
            "input[name='username']",
            "input[placeholder*='שם']",  # Hebrew for username
            "input[placeholder*='user']",
            "input:not([type='password'])",
            "//input[@type='text']",
        ]

        for selector in selectors:
            try:
                if selector.startswith('//'):
                    username_field = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.XPATH, selector))
                    )
                else:
                    username_field = WebDriverWait(driver, 3).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, selector))
                    )
                if username_field:
                    print(f"✓ Found username field with: {selector}")
                    break
            except:
                continue

        if not username_field:
            print("✗ Could not find username field!")
            print("❓ Please login manually in the browser...")
            input("   Press ENTER after you've logged in... ")
        else:
            # Enter username
            print("\n5. Entering credentials...")
            username_field.click()
            time.sleep(0.5)
            username_field.clear()
            username_field.send_keys(username)
            print(f"✓ Entered username: {username}")
            time.sleep(1)

            # Find password field
            password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
            password_field.click()
            time.sleep(0.5)
            password_field.clear()
            password_field.send_keys(password)
            print(f"✓ Entered password")
            time.sleep(1)

            # Submit form - try Enter key first (more reliable than finding button)
            print("\n6. Submitting login form...")
            password_field.send_keys(Keys.RETURN)
            print("✓ Submitted form (pressed Enter)")

            # Wait for captcha and login
            print("\n7. Waiting for login to complete...")
            print("⚠️  If there's a CAPTCHA, please solve it in the browser!")
            print("⚠️  Waiting up to 2 minutes...")

            # Wait for URL to change or token to appear
            start_time = time.time()
            logged_in = False

            while time.time() - start_time < 120:  # 2 minutes
                current_url = driver.current_url

                # Check if URL changed (logged in)
                if 'login' not in current_url.lower():
                    print(f"✓ Login successful - URL changed to: {current_url[:50]}...")
                    logged_in = True
                    break

                # Check for token in cookies
                cookies = driver.get_cookies()
                for cookie in cookies:
                    if cookie['name'] == 'webToken':
                        print("✓ Found webToken in cookies!")
                        logged_in = True
                        break

                if logged_in:
                    break

                time.sleep(2)

            if not logged_in:
                print("⚠️  Login didn't complete automatically")
                print("    Continue manually in browser and come back here...")
                input("    Press ENTER when you're logged in... ")

        # Extract token
        print("\n8. Extracting token from cookies...")
        time.sleep(3)  # Give it time to set all cookies

        cookies = driver.get_cookies()
        web_token = None

        for cookie in cookies:
            if cookie['name'] == 'webToken':
                web_token = cookie['value']
                break

        if not web_token:
            print("✗ Could not find webToken cookie!")
            print("   Make sure you're logged in successfully")
            driver.quit()
            return False

        print(f"✓ Token extracted: {web_token[:50]}...")

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
        print(f"✓ Token valid for ~24 hours")
        print()
        print("=" * 60)
        print("SUCCESS! Token cached. You can now run:")
        print("  python smartschool_monitor_v2.py")
        print("=" * 60)

        # Close browser
        print("\nClosing browser in 5 seconds...")
        time.sleep(5)
        driver.quit()

        return True

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

        print("\n⚠️  Error occurred, but browser is still open")
        print("    You can complete login manually")
        input("    Press ENTER after logging in... ")

        # Try to extract token anyway
        try:
            cookies = driver.get_cookies()
            for cookie in cookies:
                if cookie['name'] == 'webToken':
                    web_token = cookie['value']

                    # Save it
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

                    with open(cache_file, 'w') as f:
                        json.dump(cache, f, indent=2)

                    print("✓ Token extracted and saved!")
                    driver.quit()
                    return True
        except:
            pass

        driver.quit()
        return False

if __name__ == "__main__":
    try:
        auto_login()
    except KeyboardInterrupt:
        print("\n\nCancelled by user")
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
