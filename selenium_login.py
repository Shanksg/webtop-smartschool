#!/usr/bin/env python3
"""
Selenium-based login for SmartSchool
Handles reCAPTCHA by waiting for user to solve it
"""

import time
import json
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from loguru import logger


class SmartSchoolSeleniumLogin:
    """Selenium-based login handler for SmartSchool"""

    def __init__(self, headless=False):
        """
        Initialize Selenium browser

        Args:
            headless: Run browser in headless mode (no window).
                      Set to False for first login to solve captcha.
        """
        self.headless = headless
        self.driver = None

    def setup_driver(self):
        """Setup Chrome driver with options"""
        try:
            options = uc.ChromeOptions()

            if self.headless:
                options.add_argument('--headless')

            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')

            self.driver = uc.Chrome(options=options, use_subprocess=True)
            logger.info("Chrome driver initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to setup Chrome driver: {e}")
            return False

    def login(self, username, password, timeout=300):
        """
        Login to SmartSchool with Selenium

        Args:
            username: SmartSchool username
            password: SmartSchool password
            timeout: Max time to wait for login (default 5 minutes for captcha)

        Returns:
            dict with token and student_params, or None on failure
        """
        try:
            if not self.driver:
                if not self.setup_driver():
                    return None

            logger.info(f"Logging in as {username}")

            # Navigate to login page
            login_url = "https://webtop.smartschool.co.il/account/login"
            self.driver.get(login_url)
            logger.info("Loaded login page")

            # Wait for page to load
            time.sleep(3)

            # Find and fill username field
            logger.info("Looking for username field...")
            username_field = WebDriverWait(self.driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[name='username'], input[id*='user']"))
            )
            username_field.clear()
            username_field.send_keys(username)
            logger.info("Username entered")

            # Find and fill password field
            password_field = self.driver.find_element(By.CSS_SELECTOR, "input[type='password'], input[name='password']")
            password_field.clear()
            password_field.send_keys(password)
            logger.info("Password entered")

            # Find and click login button
            login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit'], button[id*='login'], input[type='submit']")
            login_button.click()
            logger.info("Login button clicked")

            # Wait for user to solve captcha and complete login
            logger.warning("⚠️  PLEASE SOLVE THE CAPTCHA IN THE BROWSER WINDOW!")
            logger.warning("    Waiting up to 5 minutes for login to complete...")

            # Wait for successful login (URL change or token in cookies)
            start_time = time.time()
            while time.time() - start_time < timeout:
                # Check if URL changed (logged in)
                current_url = self.driver.current_url
                if 'login' not in current_url.lower():
                    logger.info("Login successful - URL changed")
                    break

                # Check for webToken cookie
                cookies = self.driver.get_cookies()
                web_token = None
                for cookie in cookies:
                    if cookie['name'] == 'webToken':
                        web_token = cookie['value']
                        logger.info("Found webToken cookie")
                        break

                if web_token:
                    break

                time.sleep(2)
            else:
                logger.error("Login timeout - captcha not solved or login failed")
                return None

            # Extract token from cookies
            cookies = self.driver.get_cookies()
            web_token = None
            for cookie in cookies:
                if cookie['name'] == 'webToken':
                    web_token = cookie['value']
                    break

            if not web_token:
                logger.error("webToken not found in cookies after login")
                return None

            logger.info(f"Got webToken: {web_token[:50]}...")

            # Now we need to get student parameters
            # Navigate to homework page or API call to get student info
            student_params = self.get_student_params()

            if not student_params:
                logger.warning("Could not get student parameters, you'll need to set them manually")

            return {
                'token': web_token,
                'student_params': student_params
            }

        except Exception as e:
            logger.error(f"Login failed: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_student_params(self):
        """
        Try to extract student parameters from the page or API calls

        Returns:
            dict with studentID, classCode, etc. or None
        """
        try:
            # Wait for page to load
            time.sleep(5)

            # Method 1: Check localStorage
            try:
                local_storage = self.driver.execute_script("return window.localStorage;")
                logger.debug(f"localStorage: {local_storage}")

                # Look for student info in localStorage
                for key, value in local_storage.items():
                    if 'student' in key.lower() or 'user' in key.lower():
                        try:
                            data = json.loads(value)
                            logger.info(f"Found student data in localStorage: {key}")
                            return self.extract_params_from_data(data)
                        except:
                            pass
            except Exception as e:
                logger.debug(f"Could not access localStorage: {e}")

            # Method 2: Intercept API calls (check browser network logs)
            try:
                logs = self.driver.get_log('performance')
                for log in logs:
                    message = json.loads(log['message'])
                    method = message.get('message', {}).get('method', '')

                    if 'Network.responseReceived' in method:
                        params = message.get('message', {}).get('params', {})
                        response_url = params.get('response', {}).get('url', '')

                        if 'PupilCard' in response_url or 'student' in response_url.lower():
                            logger.info(f"Found relevant API call: {response_url}")
                            # You would need to fetch the response body here
            except Exception as e:
                logger.debug(f"Could not check network logs: {e}")

            # Method 3: Navigate to homework page and intercept request
            logger.info("Navigating to homework page to capture parameters...")
            try:
                # Enable network logging
                self.driver.execute_cdp_cmd('Network.enable', {})

                # Navigate to a page that will trigger the homework API
                self.driver.get("https://webtop.smartschool.co.il/")
                time.sleep(5)

                # Check for API calls in performance logs
                # This is simplified - in production you'd need to properly intercept

            except Exception as e:
                logger.debug(f"Could not navigate to homework page: {e}")

            logger.warning("Could not automatically extract student parameters")
            logger.warning("You'll need to set them manually in config")
            return None

        except Exception as e:
            logger.error(f"Failed to get student params: {e}")
            return None

    def extract_params_from_data(self, data):
        """Extract relevant student parameters from data"""
        params = {}

        # Try to extract common fields
        field_mapping = {
            'studentID': ['studentID', 'student_id', 'id', 'userId'],
            'studentName': ['studentName', 'student_name', 'name', 'fullName'],
            'classCode': ['classCode', 'class_code', 'classNumber'],
            'studyYear': ['studyYear', 'study_year', 'year'],
        }

        for param_name, possible_keys in field_mapping.items():
            for key in possible_keys:
                if key in data:
                    params[param_name] = data[key]
                    break

        return params if params else None

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            logger.info("Browser closed")


def test_login():
    """Test the Selenium login"""
    import yaml
    from pathlib import Path

    # Load credentials
    config_path = Path("config/config.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    student = config['students'][0]
    username = student['username']
    password = student['password']

    print("=" * 60)
    print("Testing Selenium Login")
    print("=" * 60)
    print(f"Username: {username}")
    print("⚠️  A browser window will open")
    print("⚠️  Please solve the captcha when it appears!")
    print("=" * 60)

    login_handler = SmartSchoolSeleniumLogin(headless=False)

    try:
        result = login_handler.login(username, password)

        if result:
            print("\n✓ Login successful!")
            print(f"Token: {result['token'][:50]}...")

            if result['student_params']:
                print(f"Student params: {result['student_params']}")
            else:
                print("⚠️  Student params not found - you'll need to set manually")

            # Save to file for testing
            with open('login_result.json', 'w') as f:
                json.dump(result, f, indent=2)
            print("\n✓ Saved to login_result.json")

        else:
            print("\n✗ Login failed!")

    finally:
        # Keep browser open for 10 seconds so you can see the result
        print("\nClosing browser in 10 seconds...")
        time.sleep(10)
        login_handler.close()


if __name__ == "__main__":
    test_login()
