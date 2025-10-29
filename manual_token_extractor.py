#!/usr/bin/env python3
"""
Manual Token Extractor for SmartSchool Monitor

This script helps you manually login to SmartSchool and extract the authentication token.
The token is then saved to the cache file and can be reused by the monitoring script for 23 hours.

Usage:
    python manual_token_extractor.py

Instructions:
1. Run this script
2. A browser window will open to the SmartSchool login page
3. Complete the login manually (including reCAPTCHA)
4. After successful login, wait a few seconds
5. The script will automatically extract and save the token
6. Close the browser when prompted
"""

import json
import time
from datetime import datetime
from pathlib import Path
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from loguru import logger

def extract_token_manually(username):
    """Open browser for manual login and extract token"""

    # Setup paths
    config_dir = Path("/app/config") if Path("/app/config").exists() else Path("./config")
    token_file = config_dir / "token_cache.json"

    logger.info(f"Starting manual token extraction for {username}")
    logger.info("A browser window will open - please complete the login manually")

    # Setup Chrome
    options = uc.ChromeOptions()
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')

    driver = None

    try:
        driver = uc.Chrome(options=options, use_subprocess=True)
        logger.info("Browser opened")

        # Navigate to login page
        login_url = "https://webtop.smartschool.co.il/account/login"
        driver.get(login_url)
        logger.info("Navigated to login page")

        print("\n" + "="*70)
        print("PLEASE LOGIN MANUALLY NOW")
        print("="*70)
        print("\n1. Complete the login form")
        print("2. Solve the reCAPTCHA challenge")
        print("3. Wait for the page to load after login")
        print("4. Keep the browser open until this script confirms token extraction")
        print("\n" + "="*70 + "\n")

        # Wait for user to login
        logger.info("Waiting for manual login...")
        start_time = time.time()
        login_successful = False

        while time.time() - start_time < 300:  # 5 minute timeout
            current_url = driver.current_url.lower()

            # Check if we've left the login page
            if 'login' not in current_url and 'webtop.smartschool.co.il' in current_url:
                logger.info(f"Login detected! Current URL: {driver.current_url}")
                login_successful = True
                break

            time.sleep(2)

        if not login_successful:
            logger.error("Login was not detected within timeout period")
            return False

        # Give time for all cookies to be set
        logger.info("Waiting for tokens to be set...")
        time.sleep(5)

        # The token is likely set for the API server domain, not the main site
        # Let's try to trigger an API call or navigate to the API server
        logger.info("Triggering API call to set token cookie on API server domain...")

        try:
            # Execute JavaScript to make an API call from the page
            # This will cause the browser to set the cookie for the API domain
            driver.execute_script("""
                fetch('https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({})
                }).catch(() => {});
            """)
            logger.info("Triggered API call")
            time.sleep(3)
        except Exception as e:
            logger.warning(f"Failed to trigger API call: {e}")

        # Try navigating to different pages to trigger token setting
        pages_to_try = [
            "https://webtop.smartschool.co.il/",
            "https://webtop.smartschool.co.il/dashboard",
            "https://webtop.smartschool.co.il/account"
        ]

        for page_url in pages_to_try:
            try:
                logger.info(f"Navigating to {page_url}...")
                driver.get(page_url)
                time.sleep(2)
            except Exception as e:
                logger.warning(f"Failed to navigate to {page_url}: {e}")

        # Extract token from cookies - check both main site and API server domain
        web_token = None

        # First, check cookies on the current page (main site)
        cookies = driver.get_cookies()
        logger.info(f"Found {len(cookies)} cookies on main site")
        logger.info(f"Cookie names: {[c['name'] for c in cookies]}")

        for cookie in cookies:
            if cookie['name'] == 'webToken':
                web_token = cookie['value']
                logger.info("✓ Found webToken in main site cookies!")
                break

        # If not found, navigate to the API server domain to check cookies there
        if not web_token:
            logger.info("Token not found on main site, checking API server domain...")
            try:
                # Navigate to the API server domain
                driver.get("https://webtopserver.smartschool.co.il/")
                time.sleep(2)

                # Get cookies from API server domain
                api_cookies = driver.get_cookies()
                logger.info(f"Found {len(api_cookies)} cookies on API server")
                logger.info(f"API server cookie names: {[c['name'] for c in api_cookies]}")

                for cookie in api_cookies:
                    logger.debug(f"API Cookie: {cookie['name']} = {cookie.get('value', '')[:50]}...")
                    if cookie['name'] == 'webToken':
                        web_token = cookie['value']
                        logger.info("✓ Found webToken in API server cookies!")
                        break

                # If found, navigate back to main site
                if web_token:
                    driver.get("https://webtop.smartschool.co.il/dashboard")
                    time.sleep(1)

            except Exception as e:
                logger.warning(f"Failed to check API server cookies: {e}")

        # Try localStorage if not in cookies
        if not web_token:
            logger.info("Token not in cookies, checking localStorage...")
            try:
                all_storage = driver.execute_script("""
                    let items = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        items[key] = localStorage.getItem(key);
                    }
                    return items;
                """)

                logger.info(f"localStorage keys: {list(all_storage.keys()) if all_storage else 'empty'}")

                for key, value in (all_storage or {}).items():
                    logger.debug(f"localStorage[{key}] = {str(value)[:100]}...")
                    if 'token' in key.lower():
                        logger.info(f"Found potential token in localStorage[{key}]")
                        web_token = value
                        break
            except Exception as e:
                logger.error(f"Failed to check localStorage: {e}")

        # Try sessionStorage if still not found
        if not web_token:
            logger.info("Token not in localStorage, checking sessionStorage...")
            try:
                all_session = driver.execute_script("""
                    let items = {};
                    for (let i = 0; i < sessionStorage.length; i++) {
                        let key = sessionStorage.key(i);
                        items[key] = sessionStorage.getItem(key);
                    }
                    return items;
                """)

                logger.info(f"sessionStorage keys: {list(all_session.keys()) if all_session else 'empty'}")

                for key, value in (all_session or {}).items():
                    logger.debug(f"sessionStorage[{key}] = {str(value)[:100]}...")
                    if 'token' in key.lower():
                        logger.info(f"Found potential token in sessionStorage[{key}]")
                        web_token = value
                        break
            except Exception as e:
                logger.error(f"Failed to check sessionStorage: {e}")

        # Try to extract from any JavaScript variable in the page
        if not web_token:
            logger.info("Checking for token in JavaScript variables...")
            try:
                # Try common variable names
                for var_name in ['webToken', 'token', 'authToken', 'accessToken']:
                    try:
                        value = driver.execute_script(f"return window.{var_name};")
                        if value:
                            logger.info(f"Found token in window.{var_name}")
                            web_token = value
                            break
                    except:
                        pass
            except Exception as e:
                logger.error(f"Failed to check JavaScript variables: {e}")

        # Try to intercept network requests by making a test API call
        if not web_token:
            logger.info("Attempting to intercept token from network requests...")
            try:
                # Execute a script that will make an API call and capture the token from cookies before the call
                result = driver.execute_script("""
                    // Get all cookies in a format we can use
                    function getAllCookies() {
                        let cookies = {};
                        document.cookie.split(';').forEach(cookie => {
                            let [name, value] = cookie.trim().split('=');
                            if (name) cookies[name] = value;
                        });
                        return cookies;
                    }

                    return getAllCookies();
                """)

                logger.info(f"Cookies from document.cookie: {result}")

                if result and 'webToken' in result:
                    web_token = result['webToken']
                    logger.info("✓ Found webToken in document.cookie!")

            except Exception as e:
                logger.error(f"Failed to check document.cookie: {e}")

        if not web_token:
            logger.error("Failed to extract token from cookies, localStorage, sessionStorage, or JS variables")
            logger.info("All cookie names found: " + str([c['name'] for c in cookies]))

            # Comprehensive debug dump
            print("\n" + "="*70)
            print("DEBUG: Complete Storage Dump")
            print("="*70)

            # Dump all cookies
            print("\nAll Cookies:")
            for cookie in cookies:
                print(f"  {cookie['name']}: {cookie.get('value', '')[:100]}")

            # Dump localStorage
            try:
                all_storage = driver.execute_script("""
                    let items = {};
                    for (let i = 0; i < localStorage.length; i++) {
                        let key = localStorage.key(i);
                        items[key] = localStorage.getItem(key);
                    }
                    return items;
                """)
                print("\nLocalStorage:")
                if all_storage:
                    for key, value in all_storage.items():
                        print(f"  {key}: {str(value)[:200]}")
                else:
                    print("  (empty)")
            except Exception as e:
                print(f"  Error: {e}")

            # Dump sessionStorage
            try:
                all_session = driver.execute_script("""
                    let items = {};
                    for (let i = 0; i < sessionStorage.length; i++) {
                        let key = sessionStorage.key(i);
                        items[key] = sessionStorage.getItem(key);
                    }
                    return items;
                """)
                print("\nSessionStorage:")
                if all_session:
                    for key, value in all_session.items():
                        print(f"  {key}: {str(value)[:200]}")
                else:
                    print("  (empty)")
            except Exception as e:
                print(f"  Error: {e}")

            print("\n" + "="*70)
            print("Please check the browser's DevTools:")
            print("1. Open DevTools (F12)")
            print("2. Go to Application tab")
            print("3. Check Cookies, Local Storage, Session Storage")
            print("4. Look for any 'webToken' or 'token' values")
            print("="*70 + "\n")

            return False

        # Save token to cache
        logger.info("Saving token to cache...")

        cache = {}
        if token_file.exists():
            try:
                with open(token_file, 'r') as f:
                    cache = json.load(f)
            except:
                pass

        # Note: We don't have student_params yet, they will be provided in config
        cache[username] = {
            'token': web_token,
            'student_params': None,  # Will be read from config
            'timestamp': datetime.now().isoformat()
        }

        token_file.parent.mkdir(exist_ok=True, parents=True)
        with open(token_file, 'w') as f:
            json.dump(cache, f, indent=2)

        print("\n" + "="*70)
        print("✓ SUCCESS! Token extracted and saved!")
        print("="*70)
        print(f"\nToken: {web_token[:50]}...")
        print(f"Saved to: {token_file}")
        print(f"\nThis token will be valid for ~23 hours")
        print("You can now run the monitoring script: python smartschool_monitor_v2.py")
        print("\n" + "="*70 + "\n")

        logger.info("Token extraction successful!")

        # Keep browser open for a moment
        time.sleep(3)

        return True

    except Exception as e:
        logger.error(f"Error during token extraction: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        if driver:
            logger.info("Closing browser...")
            driver.quit()


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SmartSchool Manual Token Extractor")
    print("="*70 + "\n")

    username = input("Enter your SmartSchool username: ").strip()

    if not username:
        print("Error: Username is required")
        exit(1)

    success = extract_token_manually(username)

    if success:
        print("\n✓ Token successfully extracted and cached!")
        exit(0)
    else:
        print("\n✗ Failed to extract token")
        exit(1)
