import os
import json
import requests
import schedule
import time
from datetime import datetime
from pathlib import Path
from loguru import logger
import apprise
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import unquote
import hashlib
import re

# Playwright for browser-based scraping (fallback when API is blocked)
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning("playwright not installed. Browser scraping unavailable. Install with: pip install playwright && playwright install chromium")

# MQTT support (optional)
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    MQTT_AVAILABLE = False
    logger.warning("paho-mqtt not installed. MQTT entities will not be created. Install with: pip install paho-mqtt")

# Configure logging
log_dir = Path("/app/logs") if Path("/app").exists() else Path("./logs")
log_dir.mkdir(exist_ok=True)
logger.add(f"{log_dir}/smartschool-monitor.log", rotation="500 MB", retention="7 days")

class SmartSchoolMonitor:
    def __init__(self):
        self.config_path = Path("/app/config/config.yaml") if Path("/app/config").exists() else Path("./config/config.yaml")
        self.state_file = Path("/app/config/homework_state.json") if Path("/app/config").exists() else Path("./config/homework_state.json")
        self.token_file = Path("/app/config/token_cache.json") if Path("/app/config").exists() else Path("./config/token_cache.json")
        self.students = []
        self.notifiers = []
        self.mqtt_client = None
        self.load_config()
        self.setup_notifiers()
        self.setup_mqtt()
        self.load_state()

    def load_config(self):
        """Load configuration from YAML file"""
        try:
            import yaml
            if not self.config_path.exists():
                logger.error(f"Config file not found: {self.config_path}")
                raise FileNotFoundError(f"Config file not found: {self.config_path}")

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            self.students = config.get('students', [])
            logger.info(f"Loaded {len(self.students)} students from config")
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            raise

    def setup_notifiers(self):
        """Setup Apprise notifiers from environment variable"""
        notifiers_str = os.getenv('NOTIFIERS', '')
        if not notifiers_str:
            logger.warning("No NOTIFIERS environment variable set")
            return

        self.apobj = apprise.Apprise()
        for notifier in notifiers_str.split(','):
            notifier = notifier.strip()
            if notifier:
                if self.apobj.add(notifier):
                    logger.info(f"Added notifier: {notifier}")
                else:
                    logger.error(f"Failed to add notifier: {notifier}")

    def setup_mqtt(self):
        """Setup MQTT client for Home Assistant entity creation"""
        if not MQTT_AVAILABLE:
            logger.info("MQTT not available - skipping MQTT entity setup")
            return

        mqtt_broker = os.getenv('MQTT_BROKER', '')
        if not mqtt_broker:
            logger.info("MQTT_BROKER not configured - skipping MQTT entity setup")
            return

        try:
            mqtt_port = int(os.getenv('MQTT_PORT', '1883'))
            mqtt_user = os.getenv('MQTT_USER', '')
            mqtt_pass = os.getenv('MQTT_PASS', '')

            self.mqtt_client = mqtt.Client()

            if mqtt_user and mqtt_pass:
                self.mqtt_client.username_pw_set(mqtt_user, mqtt_pass)

            self.mqtt_client.connect(mqtt_broker, mqtt_port, 60)
            self.mqtt_client.loop_start()

            logger.info(f"✓ MQTT connected to {mqtt_broker}:{mqtt_port}")

        except Exception as e:
            logger.error(f"Failed to setup MQTT: {e}")
            self.mqtt_client = None

    def publish_mqtt_discovery(self, student_name):
        """Publish MQTT discovery messages for Home Assistant"""
        if not self.mqtt_client:
            return

        try:
            # Create a safe ASCII device ID from student name (use hash for Hebrew names)
            import hashlib
            name_hash = hashlib.md5(student_name.encode()).hexdigest()[:8]
            device_id = f"student_{name_hash}"

            # Device info shared by all entities
            device_info = {
                "identifiers": [f"smartschool_{device_id}"],
                "name": f"SmartSchool - {student_name}",
                "manufacturer": "SmartSchool Monitor",
                "model": "Homework Tracker"
            }

            # 1. Homework Count Sensor
            count_config = {
                "name": f"SmartSchool {student_name} Homework Count",
                "unique_id": f"smartschool_{device_id}_homework_count",
                "state_topic": f"smartschool/{device_id}/state",
                "value_template": "{{ value_json.count }}",
                "icon": "mdi:book-open-variant",
                "device": device_info
            }
            self.mqtt_client.publish(
                f"homeassistant/sensor/smartschool_{device_id}_count/config",
                json.dumps(count_config),
                retain=True
            )

            # 2. Homework Details Sensor
            details_config = {
                "name": f"SmartSchool {student_name} Homework Details",
                "unique_id": f"smartschool_{device_id}_homework_details",
                "state_topic": f"smartschool/{device_id}/state",
                "value_template": "{{ value_json.details }}",
                "icon": "mdi:text-box-multiple",
                "device": device_info
            }
            self.mqtt_client.publish(
                f"homeassistant/sensor/smartschool_{device_id}_details/config",
                json.dumps(details_config),
                retain=True
            )

            # 3. Last Check Sensor
            last_check_config = {
                "name": f"SmartSchool {student_name} Last Check",
                "unique_id": f"smartschool_{device_id}_last_check",
                "state_topic": f"smartschool/{device_id}/state",
                "value_template": "{{ value_json.last_check }}",
                "icon": "mdi:clock-check",
                "device_class": "timestamp",
                "device": device_info
            }
            self.mqtt_client.publish(
                f"homeassistant/sensor/smartschool_{device_id}_last_check/config",
                json.dumps(last_check_config),
                retain=True
            )

            logger.info(f"Published MQTT discovery for {student_name}")

        except Exception as e:
            logger.error(f"Failed to publish MQTT discovery: {e}")

    def publish_mqtt_state(self, student_name, homework_list):
        """Publish current homework state to MQTT"""
        if not self.mqtt_client:
            return

        try:
            # Use same device ID as discovery
            import hashlib
            name_hash = hashlib.md5(student_name.encode()).hexdigest()[:8]
            device_id = f"student_{name_hash}"

            # Filter to today's homework
            today = datetime.now().strftime('%Y-%m-%d')
            today_homework = [hw for hw in homework_list if hw.get('date', '')[:10] == today]

            # Format homework details
            if today_homework:
                details = f"Today's homework for {student_name}:\n\n"
                for idx, hw in enumerate(today_homework, 1):
                    subject = hw.get('subject', 'Unknown')
                    homework = hw.get('homework', '')
                    teacher = hw.get('teacher', '')
                    details += f"{idx}. {subject} - {teacher}\n"
                    details += f"   {homework[:200]}\n"
                    if len(homework) > 200:
                        details += "   ...\n"
                    details += "\n"
            else:
                details = f"No homework for today ({today})"

            # Publish state
            state = {
                "count": len(today_homework),
                "details": details,
                "last_check": datetime.now().isoformat()
            }

            self.mqtt_client.publish(
                f"smartschool/{device_id}/state",
                json.dumps(state),
                retain=True
            )

            logger.info(f"Published MQTT state for {student_name}: {len(today_homework)} homework items")

        except Exception as e:
            logger.error(f"Failed to publish MQTT state: {e}")

    def load_state(self):
        """Load previous homework state"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.homework_state = json.load(f)
                logger.info("Loaded previous homework state")
            except Exception as e:
                logger.error(f"Failed to load state: {e}")
                self.homework_state = {}
        else:
            self.homework_state = {}

    def save_state(self):
        """Save homework state to file"""
        try:
            self.state_file.parent.mkdir(exist_ok=True, parents=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.homework_state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save state: {e}")

    def load_token_cache(self, username):
        """Load cached token for a user"""
        if not self.token_file.exists():
            return None

        try:
            with open(self.token_file, 'r') as f:
                cache = json.load(f)

            user_cache = cache.get(username)
            if not user_cache:
                return None

            # Check if token is expired (tokens usually last 24 hours)
            cached_time = datetime.fromisoformat(user_cache['timestamp'])
            if (datetime.now() - cached_time).total_seconds() > 23 * 3600:  # 23 hours
                logger.info(f"Cached token for {username} is expired (time-based)")
                return None

            # URL-decode the token if it's encoded
            token = user_cache.get('token', '')
            if token and '%' in token:
                user_cache['token'] = unquote(token)
                logger.debug("Decoded URL-encoded token from cache")

            logger.info(f"Using cached token for {username}")
            return user_cache

        except Exception as e:
            logger.error(f"Failed to load token cache: {e}")
            return None

    def validate_token(self, token, student_params):
        """Test if token is still valid - skip validation since API is blocked, will validate during fetch"""
        # Since API returns "view is blocked" even for valid tokens,
        # we skip validation here and let the Playwright fetch determine if token works
        logger.info("Skipping token validation (will validate during fetch)")
        return True

    def save_token_cache(self, username, token, student_params):
        """Save token to cache"""
        try:
            cache = {}
            if self.token_file.exists():
                with open(self.token_file, 'r') as f:
                    cache = json.load(f)

            cache[username] = {
                'token': token,
                'student_params': student_params,
                'timestamp': datetime.now().isoformat()
            }

            self.token_file.parent.mkdir(exist_ok=True, parents=True)
            with open(self.token_file, 'w') as f:
                json.dump(cache, f, indent=2)

            logger.info(f"Saved token cache for {username}")

        except Exception as e:
            logger.error(f"Failed to save token cache: {e}")

    def request_manual_token(self, username):
        """Request user to manually provide token"""
        logger.info(f"Token required for user: {username}")
        logger.info("Please add your token to: config/token.txt")

        # Check if token file exists
        token_file = Path("config/token.txt")
        if token_file.exists():
            token = token_file.read_text().strip()
            if token:
                logger.info("Found token in config/token.txt")
                # URL-decode the token if it's encoded
                if '%' in token:
                    token = unquote(token)
                    logger.debug("Decoded URL-encoded token from file")
                return token

        return None

    def get_homework(self, token, student_params):
        """
        Fetch homework from SmartSchool API

        Args:
            token: webToken from login
            student_params: dict with studentID, classCode, etc.
        """
        try:
            api_url = "https://webtopserver.smartschool.co.il/server/api/PupilCard/GetPupilLessonsAndHomework"

            session = requests.Session()
            session.verify = False

            # Set cookies
            logger.debug(f"Token length: {len(token)}, starts with: {token[:50]}...")
            session.cookies.set('webToken', token)
            session.cookies.set('input', '0')

            # Set headers like browser
            headers = {
                'Content-Type': 'application/json',
                'Accept': 'application/json, text/plain, */*',
                'language': 'he',
                'rememberme': '0',
                'origin': 'https://webtop.smartschool.co.il',
                'referer': 'https://webtop.smartschool.co.il/',
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
            }

            logger.debug(f"Posting to API with student_params: {student_params}")

            # POST with student parameters
            response = session.post(api_url, json=student_params, headers=headers, timeout=10)
            response.raise_for_status()

            data = response.json()
            logger.debug(f"API response status: {data.get('status')}, full response: {data}")

            if data.get('status') == True:
                logger.info(f"Successfully retrieved homework data")
                return data.get('data', [])
            else:
                # Check for "Invalid Request" error in Hebrew (often sent when blocked)
                # The server returns "Error: בקשה לא-חוקית"
                if "בקשה לא-חוקית" in str(data):
                    logger.error(f"API returned 'Invalid Request' (בקשה לא-חוקית) - user may be blocked or token expired")
                else:
                    error_desc = data.get('errorDescription', 'Unknown error')
                    logger.error(f"API returned error: {error_desc}")
                return None

        except Exception as e:
            logger.error(f"Failed to get homework: {e}")
            return None

    def extract_homework_items(self, homework_data):
        """Extract actual homework from the schedule data"""
        homework_items = []

        if not homework_data:
            return homework_items

        for day in homework_data:
            date = day.get('date', '')
            hours_data = day.get('hoursData', [])

            for hour in hours_data:
                schedule = hour.get('scheduale', [])

                for item in schedule:
                    homework_text = item.get('homeWork') or ''
                    if homework_text:
                        homework_text = homework_text.strip()

                    if homework_text:  # Only include if there's actual homework
                        homework_items.append({
                            'date': date,
                            'subject': item.get('subject_name') or 'Unknown',
                            'teacher': item.get('teacher') or 'Unknown',
                            'homework': homework_text,
                            'description': item.get('descClass') or ''
                        })

        return homework_items

    def get_homework_playwright(self, token):
        """
        Scrape homework from the website using Playwright browser automation.
        This is used when the API returns 'view is blocked'.
        """
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("Playwright not available for browser scraping")
            return None

        try:
            logger.info("Using Playwright browser to scrape homework...")

            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    locale='he-IL',
                )

                # Set the webToken cookie
                context.add_cookies([{
                    'name': 'webToken',
                    'value': token,
                    'domain': '.smartschool.co.il',
                    'path': '/',
                }])

                page = context.new_page()

                # Navigate to the pupil card page
                logger.info("Navigating to pupil card page...")
                page.goto('https://webtop.smartschool.co.il/pupilcard', timeout=30000)

                # Wait for content to load
                time.sleep(5)

                # Get page text content
                body_text = page.inner_text('body')

                browser.close()

                # Parse the homework from page text
                return self.parse_homework_from_text(body_text)

        except Exception as e:
            logger.error(f"Playwright scraping failed: {e}")
            return None

    def parse_homework_from_text(self, text):
        """Parse homework items from page text content"""
        homework_items = []
        today = datetime.now().strftime('%Y-%m-%d')

        # Split by "שיעור" (lesson) to find lesson blocks
        # Pattern: subject followed by lesson number, teacher, and homework
        lines = text.split('\n')

        current_subject = None
        current_teacher = None
        in_homework = False
        homework_text = ""

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check for subject headers (common subjects)
            subjects = ['מתמטיקה', 'חשבון', 'גיאומטריה', 'עברית', 'שפה', 'אנגלית',
                       'מדע', 'מדעים', 'היסטוריה', 'גאוגרפיה', 'תנ"ך', 'ספרות',
                       'מדע וטכנולוגיה', 'חינוך גופני', 'אמנות', 'מוזיקה']

            for subj in subjects:
                if line.startswith(subj) or line == subj:
                    current_subject = line
                    break

            # Look for "שיעור X" pattern
            if re.match(r'שיעור \d+', line):
                pass  # Just a lesson number marker

            # Check for teacher name (usually comes after lesson number)
            # Hebrew names pattern
            if re.match(r'^[א-ת]+(\')?[א-ת]* [א-ת]+$', line):
                current_teacher = line

            # Look for homework marker
            if 'שיעורי בית:' in line or 'שיעורי בית' in line:
                in_homework = True
                # Extract homework after the colon
                if ':' in line:
                    hw = line.split(':', 1)[1].strip()
                    if hw and hw != 'לא הוזן':
                        homework_text = hw

            # If we found homework, add it
            if homework_text and current_subject:
                homework_items.append({
                    'date': today,
                    'subject': current_subject,
                    'teacher': current_teacher or 'Unknown',
                    'homework': homework_text,
                    'description': ''
                })
                homework_text = ""
                in_homework = False

            i += 1

        logger.info(f"Parsed {len(homework_items)} homework items from page")
        return homework_items

    def hash_homework(self, homework_item):
        """Create a hash of homework item to detect changes"""
        try:
            hw_str = json.dumps(homework_item, sort_keys=True, ensure_ascii=False)
            return hashlib.md5(hw_str.encode()).hexdigest()
        except:
            return None

    def check_homework(self, student_name, username, password, student_params):
        """Check for new homework for a student"""
        try:
            token = None
            need_new_token = False

            # Try to use cached token first
            cached = self.load_token_cache(username)

            if cached:
                token = cached['token']
                if not student_params:
                    student_params = cached.get('student_params')

                # Validate token before using
                logger.info(f"Found cached token for {student_name}, validating...")
                if not self.validate_token(token, student_params):
                    logger.warning(f"Cached token for {student_name} is invalid, need new login")
                    need_new_token = True
                    token = None
            else:
                logger.info(f"No cached token for {student_name}")
                need_new_token = True

            # Get new token if needed
            if need_new_token:
                logger.info(f"Need new token for {student_name}")
                token = self.request_manual_token(username)

                if not token:
                    logger.error(f"No token available for {student_name}")
                    logger.error(f"Please provide token in config/token.txt")
                    return

                # Cache the new token
                self.save_token_cache(username, token, student_params)
                logger.info(f"✓ Token cached for {student_name}")

            # Get homework - try Playwright directly since API is usually blocked
            homework_items = []

            # Try API first if we have student_params (might work sometimes)
            if student_params:
                homework_data = self.get_homework(token, student_params)
                if homework_data:
                    homework_items = self.extract_homework_items(homework_data)
                    logger.info(f"Got {len(homework_items)} homework items from API")

            # Use Playwright if API returned nothing
            if not homework_items:
                logger.info("Using Playwright browser scraping...")
                homework_items = self.get_homework_playwright(token)

                if homework_items:
                    logger.info(f"Got {len(homework_items)} homework items from Playwright")
                else:
                    logger.warning(f"No homework data for {student_name} from any source")
                    return

            # Initialize state for this student if needed
            if student_name not in self.homework_state:
                self.homework_state[student_name] = {}

            # Check for new homework
            new_homework = []
            current_hashes = {}

            for item in homework_items:
                item_hash = self.hash_homework(item)
                if not item_hash:
                    continue

                current_hashes[item_hash] = item

                # Check if this is new homework
                if item_hash not in self.homework_state[student_name]:
                    new_homework.append(item)
                    self.homework_state[student_name][item_hash] = {
                        'detected_at': datetime.now().isoformat(),
                        'item': item
                    }
                    logger.info(f"New homework detected: {item['subject']}")

            # Remove old homework from state
            self.homework_state[student_name] = {
                k: v for k, v in self.homework_state[student_name].items()
                if k in current_hashes
            }

            # Publish MQTT discovery (first time) and state (always)
            # This creates/updates Home Assistant entities
            logger.debug("Publishing MQTT discovery...")
            self.publish_mqtt_discovery(student_name)
            logger.debug("Publishing MQTT state...")
            self.publish_mqtt_state(student_name, homework_items)
            logger.debug("MQTT publishing done")

            # Send notifications if new homework found
            if new_homework:
                logger.info(f"Sending notification for {len(new_homework)} new items...")
                self.send_notification(student_name, new_homework)
                logger.info("Notification sent")
            else:
                logger.info("No new homework, skipping notification")

            # Save state
            logger.debug("Saving state...")
            self.save_state()
            logger.info(f"Check complete for {student_name}")

        except Exception as e:
            logger.error(f"Error checking homework for {student_name}: {e}")
            import traceback
            traceback.print_exc()

    def send_notification(self, student_name, homework_list):
        """Send notification via webhook or Apprise"""
        try:
            if not hasattr(self, 'apobj') or len(self.apobj) == 0:
                logger.warning("No notifiers configured")
                return

            # Filter to only today's homework
            today = datetime.now().strftime('%Y-%m-%d')
            today_homework = [hw for hw in homework_list if hw.get('date', '')[:10] == today]

            if not today_homework:
                logger.info(f"No homework for today ({today}), skipping notification")
                return

            # Format homework message
            message = f"📚 New homework for {student_name} (Today: {today}):\n\n"

            for idx, hw in enumerate(today_homework, 1):
                date_str = hw.get('date', '')[:10]  # Just the date part
                subject = hw.get('subject', 'Unknown')
                homework = hw.get('homework', '')
                teacher = hw.get('teacher', '')

                message += f"{idx}. {subject} ({date_str})\n"
                message += f"   👨‍🏫 {teacher}\n"
                message += f"   📝 {homework[:200]}\n"  # Limit length
                if len(homework) > 200:
                    message += f"   ...\n"
                message += "\n"

            title = f"SmartSchool Homework - {student_name}"

            logger.info(f"Sending notification: {title}")

            # Use Apprise to send to all configured notifiers
            # Apprise handles different protocols (webhook, MQTT, etc.) automatically
            self.apobj.notify(
                body=message,
                title=title
            )

        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    def _send_webhook_notification(self, notifier_url, title, message):
        """Send notification directly to webhook"""
        try:
            # Parse the webhook URL
            # Format: json://host:port/path or jsons://host:port/path
            if notifier_url.startswith('jsons://'):
                url = 'https://' + notifier_url[8:]
                verify_ssl = True
            elif notifier_url.startswith('json://'):
                url = 'http://' + notifier_url[7:]
                verify_ssl = True
            else:
                logger.error(f"Unknown notifier format: {notifier_url}")
                return

            # Check for verify=no parameter
            if '?verify=no' in url:
                url = url.replace('?verify=no', '')
                verify_ssl = False

            # Prepare the exact format that works with curl
            payload = {
                "title": title,
                "message": message
            }

            logger.info(f"Sending webhook to: {url}")
            logger.debug(f"Payload: {payload}")

            # Send the request
            response = requests.post(
                url,
                json=payload,
                headers={'Content-Type': 'application/json'},
                verify=verify_ssl,
                timeout=10
            )

            if response.status_code == 200:
                logger.info("✓ Webhook notification sent successfully")
            else:
                logger.error(f"Webhook returned status {response.status_code}: {response.text}")

        except Exception as e:
            logger.error(f"Failed to send webhook notification: {e}")
            import traceback
            traceback.print_exc()

    def schedule_checks(self):
        """Schedule homework checks at specific times"""
        schedules_str = os.getenv('SCHEDULES', '12:00,16:00,20:00')
        schedules = [s.strip() for s in schedules_str.split(',')]

        logger.info(f"Scheduling checks at: {schedules}")

        for schedule_time in schedules:
            schedule.every().day.at(schedule_time).do(self.run_all_checks)
            logger.info(f"Scheduled check at {schedule_time}")

    def run_all_checks(self):
        """Run homework checks for all students"""
        logger.info(f"Starting scheduled check at {datetime.now()}")

        for student in self.students:
            try:
                name = student.get('name', 'Unknown')
                username = student.get('username')
                password = student.get('password')
                student_params = student.get('student_params')  # Optional in config

                if not username or not password:
                    logger.warning(f"Missing credentials for {name}")
                    continue

                self.check_homework(name, username, password, student_params)

            except Exception as e:
                logger.error(f"Error checking homework for student: {e}")

            # Small delay between checks
            time.sleep(2)

    def start(self):
        """Start the monitor"""
        logger.info("Starting SmartSchool Homework Monitor v2 (Manual Token Mode)")

        self.schedule_checks()

        # Run first check immediately
        self.run_all_checks()

        # Keep scheduler running
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)
            except KeyboardInterrupt:
                logger.info("Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Scheduler error: {e}")
                time.sleep(60)


if __name__ == "__main__":
    try:
        monitor = SmartSchoolMonitor()
        monitor.start()
    except Exception as e:
        logger.error(f"Failed to start monitor: {e}")
        raise
