#!/usr/bin/env python3
"""
Fully automated login using undetected-chromedriver in headless mode
No manual interaction required
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

def fully_automated_login(headless=True):
    """Fully automated login - no user interaction"""

    print("=" * 60)
    print("SmartSchool FULLY Automated Login")
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
    print(f"Headless mode: {headless}")
    print("=" * 60)

    # Setup undetected Chrome
    print("\n1. Initializing browser...")
    options = uc.ChromeOptions()

    if headless:
        options.add_argument('--headless=new')  # New headless mode
        options.add_argument('--disable-gpu')

    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')
    options.add_argument('--window-size=1920,1080')

    # Add realistic user agent
    options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36')

    driver = uc.Chrome(options=options, use_subprocess=True, version_main=None)

    try:
        # Navigate to login page
        login_url = "https://webtop.smartschool.co.il/account/login"
        print(f"\n2. Navigating to {login_url}")
        driver.get(login_url)
        print("✓ Page loaded")

        # Wait for Angular to initialize
        print("\n3. Waiting for page initialization...")
        time.sleep(10)

        # Inject JavaScript to remove overlays and prepare page
        print("\n4. Preparing page...")
        js_prepare = """
        // Remove all overlays
        document.querySelectorAll('[class*="modal"], [class*="overlay"], [class*="cookie"]').forEach(el => el.remove());
        document.body.style.overflow = 'auto';

        // Disable Angular animations for faster processing
        if (window.angular) {
            angular.element(document.body).injector().get('$animate').enabled(false);
        }

        return 'Page prepared';
        """
        result = driver.execute_script(js_prepare)
        print(f"✓ {result}")

        # Find and fill login form
        print("\n5. Filling login form...")

        # Wait for input fields
        wait = WebDriverWait(driver, 20)

        # Find username field (try multiple selectors)
        username_field = None
        username_selectors = [
            "input[type='text']",
            "input[name='username']",
            "//input[@type='text']",
            "//input[contains(@placeholder, 'שם')]",
        ]

        for selector in username_selectors:
            try:
                if selector.startswith('//'):
                    username_field = wait.until(EC.presence_of_element_located((By.XPATH, selector)))
                else:
                    username_field = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))

                if username_field:
                    print(f"✓ Found username field")
                    break
            except:
                continue

        if not username_field:
            print("✗ Could not find username field")
            driver.save_screenshot("error_screenshot.png")
            print("✓ Saved screenshot to error_screenshot.png")
            driver.quit()
            return None

        # Fill username
        username_field.click()
        time.sleep(0.5)
        username_field.send_keys(username)
        print(f"✓ Entered username")
        time.sleep(1)

        # Find password field
        password_field = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        password_field.click()
        time.sleep(0.5)
        password_field.send_keys(password)
        print(f"✓ Entered password")
        time.sleep(1)

        # Submit form
        print("\n6. Submitting form...")
        password_field.send_keys(Keys.RETURN)
        print("✓ Form submitted")

        # Wait for login to complete or captcha to appear
        print("\n7. Waiting for login response...")

        # Check for captcha
        time.sleep(5)

        # Check if recaptcha is present
        captcha_present = False
        try:
            captcha_iframe = driver.find_elements(By.CSS_SELECTOR, "iframe[src*='recaptcha']")
            if captcha_iframe:
                print("⚠️  reCAPTCHA detected on page")
                captcha_present = True
        except:
            pass

        if captcha_present:
            print("\n" + "=" * 60)
            print("❌ CAPTCHA DETECTED - Cannot proceed automatically")
            print()
            print("OPTIONS:")
            print("1. Use browser automation with manual captcha solving:")
            print("   python auto_login_token.py")
            print()
            print("2. Extract token from your existing Chrome session:")
            print("   python extract_token_from_browser.py")
            print()
            print("3. Use a captcha solving service (2captcha.com):")
            print("   - Get API key from https://2captcha.com")
            print("   - Set environment variable: export CAPTCHA_API_KEY='your_key'")
            print("   - Re-run this script")
            print("=" * 60)
            driver.quit()
            return None

        # Wait for successful login (URL change or token in cookies)
        start_time = time.time()
        token = None

        while time.time() - start_time < 60:  # 1 minute timeout
            current_url = driver.current_url

            # Check if logged in
            if 'login' not in current_url.lower():
                print(f"✓ Login successful - redirected to: {current_url[:50]}...")
                break

            # Check for token
            cookies = driver.get_cookies()
            for cookie in cookies:
                if cookie['name'] == 'webToken' and cookie['value']:
                    token = cookie['value']
                    print("✓ Token received")
                    break

            if token:
                break

            time.sleep(2)

        # Extract final token
        print("\n8. Extracting token...")
        time.sleep(3)

        cookies = driver.get_cookies()
        web_token = None

        for cookie in cookies:
            if cookie['name'] == 'webToken':
                web_token = cookie['value']
                break

        if not web_token:
            print("✗ Could not extract token")
            print("   Login may have failed or captcha was required")
            driver.save_screenshot("login_failed.png")
            print("✓ Saved screenshot to login_failed.png")
            driver.quit()
            return None

        print(f"✓ Token extracted: {web_token[:50]}...")

        # Save token
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
        print()
        print("=" * 60)
        print("✓ SUCCESS! Fully automated login completed")
        print("=" * 60)

        driver.quit()
        return web_token

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()

        try:
            driver.save_screenshot("error.png")
            print("✓ Saved error screenshot to error.png")
        except:
            pass

        driver.quit()
        return None

if __name__ == "__main__":
    import sys

    # Check if user wants headless or with GUI
    headless = True
    if len(sys.argv) > 1 and sys.argv[1] == '--gui':
        headless = False
        print("Running with GUI (you can see the browser)")

    result = fully_automated_login(headless=headless)

    if result:
        print("\n✓ You can now run: python smartschool_monitor_v2.py")
    else:
        print("\n✗ Automated login failed")
        print("   Try with GUI to see what's happening:")
        print("   python fully_automated_login.py --gui")
