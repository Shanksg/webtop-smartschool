# 🏠 SmartSchool Monitor + Home Assistant Integration

## 📋 Table of Contents
1. [Quick Start - Running the Monitor](#quick-start)
2. [Home Assistant Integration Options](#home-assistant-integration)
3. [Method 1: Webhook Notifications](#method-1-webhook-recommended)
4. [Method 2: MQTT](#method-2-mqtt)
5. [Method 3: REST API](#method-3-rest-api)
6. [Home Assistant Automations](#home-assistant-automations)
7. [Troubleshooting](#troubleshooting)

---

## 🚀 Quick Start - Running the Monitor

### Step 1: Extract Authentication Token (Once Every 23 Hours)

```bash
python manual_token_extractor.py
```

**What happens:**
1. Browser opens to SmartSchool login page
2. You login manually (including reCAPTCHA)
3. Token is automatically extracted and cached
4. Token valid for ~23 hours

**Output:**
```
✓ SUCCESS! Token extracted and saved!
Token: W%2FT%2FKaL70Rj8h9Lt7WZn4h...
This token will be valid for ~23 hours
```

---

### Step 2: Test the Monitor

```bash
# Quick test
python test_monitor.py
```

**Expected output:**
```
✓ Token is valid
Successfully retrieved homework data
Found 5 homework items for גופר מעוז יוחנן
```

---

### Step 3: Run the Monitor

```bash
# Production mode (runs scheduled checks at 12:00, 16:00, 20:00)
python smartschool_monitor_v2.py
```

**To run in background:**
```bash
nohup python smartschool_monitor_v2.py > monitor.log 2>&1 &
```

**To stop:**
```bash
pkill -f smartschool_monitor_v2.py
```

---

## 🏠 Home Assistant Integration Options

### Comparison Table

| Method | Difficulty | Real-time | Best For |
|--------|-----------|-----------|----------|
| **Webhook** | Easy | ✅ Yes | Quick setup |
| **MQTT** | Medium | ✅ Yes | Advanced users |
| **REST API** | Easy | ✅ Yes | Token auth |

---

## Method 1: Webhook (Recommended) 🎯

### Step 1: Create Webhook in Home Assistant

**File:** `configuration.yaml`

```yaml
# Add this to configuration.yaml
automation:
  - alias: "SmartSchool Homework Received"
    trigger:
      - platform: webhook
        webhook_id: smartschool_homework_webhook
        allowed_methods:
          - POST
    action:
      - service: notify.notify
        data:
          title: "📚 {{ trigger.json.title }}"
          message: "{{ trigger.json.message }}"
      - service: persistent_notification.create
        data:
          title: "📚 {{ trigger.json.title }}"
          message: "{{ trigger.json.message }}"
```

**Restart Home Assistant** after adding this.

---

### Step 2: Get Your Webhook URL

Your webhook URL will be:
```
http://YOUR_HOME_ASSISTANT_IP:8123/api/webhook/smartschool_homework_webhook
```

**Example:**
```
http://192.168.1.100:8123/api/webhook/smartschool_homework_webhook
```

---

### Step 3: Configure SmartSchool Monitor

**Set the notification URL:**

```bash
# Replace with your Home Assistant IP
export NOTIFIERS="json://192.168.1.100:8123/api/webhook/smartschool_homework_webhook"
```

**Or add to your shell profile for persistence:**

```bash
echo 'export NOTIFIERS="json://192.168.1.100:8123/api/webhook/smartschool_homework_webhook"' >> ~/.zshrc
source ~/.zshrc
```

---

### Step 4: Test the Integration

```bash
# Clear state to trigger new homework detection
python test_new_homework.py
```

**Expected:** You should see a notification in Home Assistant! 🎉

---

## Method 2: MQTT

### Step 1: Install MQTT Broker (if not already installed)

In Home Assistant:
1. Settings → Add-ons → Add-on Store
2. Search "Mosquitto broker"
3. Install and Start

---

### Step 2: Configure MQTT in Home Assistant

**File:** `configuration.yaml`

```yaml
mqtt:
  sensor:
    - name: "SmartSchool Homework Count"
      state_topic: "smartschool/homework/count"
      unit_of_measurement: "assignments"
      icon: mdi:book-open-variant

  binary_sensor:
    - name: "SmartSchool New Homework"
      state_topic: "smartschool/homework/new"
      payload_on: "true"
      payload_off: "false"
      device_class: problem

automation:
  - alias: "SmartSchool New Homework Alert"
    trigger:
      - platform: state
        entity_id: binary_sensor.smartschool_new_homework
        to: "on"
    action:
      - service: notify.notify
        data:
          title: "📚 New Homework"
          message: "{{ states('sensor.smartschool_homework_count') }} new assignments"
```

---

### Step 3: Configure Monitor for MQTT

```bash
# Install MQTT client
pip install paho-mqtt

# Set MQTT notifier
export NOTIFIERS="mqtt://192.168.1.100:1883/smartschool/homework"
```

---

## Method 3: REST API

### Step 1: Get Long-Lived Access Token

In Home Assistant:
1. Profile (bottom left) → Security
2. Scroll to "Long-Lived Access Tokens"
3. Click "Create Token"
4. Name it "SmartSchool Monitor"
5. Copy the token (you can't see it again!)

---

### Step 2: Configure Monitor

```bash
export HA_TOKEN="your_long_lived_access_token_here"
export HA_URL="http://192.168.1.100:8123"
```

---

### Step 3: Create Custom Notification Script

**File:** `notify_homeassistant.py`

```python
import os
import requests

def notify_ha(title, message):
    ha_url = os.getenv('HA_URL', 'http://192.168.1.100:8123')
    ha_token = os.getenv('HA_TOKEN')

    if not ha_token:
        print("HA_TOKEN not set!")
        return

    # Send to Home Assistant
    url = f"{ha_url}/api/services/notify/notify"
    headers = {
        "Authorization": f"Bearer {ha_token}",
        "Content-Type": "application/json"
    }
    data = {
        "title": title,
        "message": message
    }

    response = requests.post(url, json=data, headers=headers)
    print(f"Notification sent: {response.status_code}")
```

---

## 🤖 Home Assistant Automations

### Example 1: Send to Mobile Phone

```yaml
automation:
  - alias: "SmartSchool Homework to Phone"
    trigger:
      - platform: webhook
        webhook_id: smartschool_homework_webhook
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "📚 {{ trigger.json.title }}"
          message: "{{ trigger.json.message }}"
          data:
            priority: high
            ttl: 0
            channel: homework
```

---

### Example 2: Flash Lights When New Homework

```yaml
automation:
  - alias: "Flash Lights for Homework"
    trigger:
      - platform: webhook
        webhook_id: smartschool_homework_webhook
    action:
      - service: light.turn_on
        target:
          entity_id: light.living_room
        data:
          flash: short
      - service: notify.notify
        data:
          title: "📚 {{ trigger.json.title }}"
          message: "{{ trigger.json.message }}"
```

---

### Example 3: TTS Announcement

```yaml
automation:
  - alias: "Announce Homework"
    trigger:
      - platform: webhook
        webhook_id: smartschool_homework_webhook
    action:
      - service: tts.google_translate_say
        entity_id: media_player.living_room_speaker
        data:
          message: "יש שיעורי בית חדשים"
      - service: notify.notify
        data:
          title: "📚 {{ trigger.json.title }}"
          message: "{{ trigger.json.message }}"
```

---

### Example 4: Create a To-Do List

```yaml
automation:
  - alias: "Add Homework to To-Do"
    trigger:
      - platform: webhook
        webhook_id: smartschool_homework_webhook
    action:
      - service: todo.add_item
        target:
          entity_id: todo.homework
        data:
          item: "{{ trigger.json.message }}"
```

---

## 🔄 Complete Setup Example (Webhook Method)

### 1. Home Assistant Configuration

**File:** `/config/configuration.yaml`

```yaml
# Webhook automation
automation smartschool:
  - alias: "SmartSchool New Homework"
    trigger:
      - platform: webhook
        webhook_id: smartschool_homework_webhook
        allowed_methods:
          - POST
    action:
      # Send notification
      - service: notify.notify
        data:
          title: "📚 {{ trigger.json.title }}"
          message: "{{ trigger.json.message }}"

      # Create persistent notification
      - service: persistent_notification.create
        data:
          title: "📚 {{ trigger.json.title }}"
          message: "{{ trigger.json.message }}"
          notification_id: "smartschool_homework"

      # Send to mobile
      - service: notify.mobile_app_your_phone
        data:
          title: "{{ trigger.json.title }}"
          message: "{{ trigger.json.message }}"

# Input helpers to track homework
input_number:
  smartschool_homework_count:
    name: "Homework Count"
    initial: 0
    min: 0
    max: 100
    step: 1
    icon: mdi:book-open-variant

input_text:
  smartschool_last_homework:
    name: "Last Homework"
    max: 255
    icon: mdi:clipboard-text
```

---

### 2. Monitor Setup

```bash
# 1. Set notification URL
export NOTIFIERS="json://192.168.1.100:8123/api/webhook/smartschool_homework_webhook"

# 2. Make it permanent
echo 'export NOTIFIERS="json://192.168.1.100:8123/api/webhook/smartschool_homework_webhook"' >> ~/.zshrc
source ~/.zshrc

# 3. Test it
python test_new_homework.py
```

---

### 3. Create Systemd Service (Linux) or LaunchAgent (macOS)

#### For Linux (systemd):

**File:** `/etc/systemd/system/smartschool-monitor.service`

```ini
[Unit]
Description=SmartSchool Homework Monitor
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/webtop_test/files
Environment="NOTIFIERS=json://192.168.1.100:8123/api/webhook/smartschool_homework_webhook"
ExecStart=/usr/bin/python3 smartschool_monitor_v2.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

**Enable and start:**
```bash
sudo systemctl enable smartschool-monitor
sudo systemctl start smartschool-monitor
sudo systemctl status smartschool-monitor
```

---

#### For macOS (launchd):

**File:** `~/Library/LaunchAgents/com.smartschool.monitor.plist`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.smartschool.monitor</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/yourusername/webtop_test/files/smartschool_monitor_v2.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/Users/yourusername/webtop_test/files</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>NOTIFIERS</key>
        <string>json://192.168.1.100:8123/api/webhook/smartschool_homework_webhook</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/smartschool-monitor.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/smartschool-monitor-error.log</string>
</dict>
</plist>
```

**Load it:**
```bash
launchctl load ~/Library/LaunchAgents/com.smartschool.monitor.plist
launchctl start com.smartschool.monitor
```

---

## 🐛 Troubleshooting

### Webhook Not Working?

**Test webhook manually:**
```bash
curl -X POST \
  http://192.168.1.100:8123/api/webhook/smartschool_homework_webhook \
  -H 'Content-Type: application/json' \
  -d '{
    "title": "Test Homework",
    "message": "This is a test notification"
  }'
```

---

### Check Monitor Logs

```bash
tail -f logs/smartschool-monitor.log
```

---

### Verify Token Status

```bash
python view_homework.py
```

Should show: `✅ Token valid for X hours`

---

### Test Notification

```bash
# Clear state and trigger new homework
python test_new_homework.py
```

---

## 📱 Home Assistant Dashboard Card

Add this to your Lovelace dashboard:

```yaml
type: vertical-stack
cards:
  - type: markdown
    content: |
      # 📚 SmartSchool Homework

      {{ states('input_text.smartschool_last_homework') }}

      **Total assignments:** {{ states('input_number.smartschool_homework_count') }}

  - type: button
    name: Check Now
    icon: mdi:refresh
    tap_action:
      action: call-service
      service: automation.trigger
      service_data:
        entity_id: automation.smartschool_new_homework
```

---

## ✅ Quick Start Checklist

- [ ] Extract token: `python manual_token_extractor.py`
- [ ] Add webhook to Home Assistant `configuration.yaml`
- [ ] Restart Home Assistant
- [ ] Set `NOTIFIERS` environment variable
- [ ] Test: `python test_new_homework.py`
- [ ] Check Home Assistant for notification
- [ ] Run production: `python smartschool_monitor_v2.py`
- [ ] Optional: Set up as service (systemd/launchd)

---

## 🎯 Summary

**Daily operation:**
1. Monitor runs automatically at 12:00, 16:00, 20:00
2. Checks for new homework
3. Sends notification to Home Assistant
4. Token expires after 23 hours → run `python manual_token_extractor.py`

**That's it!** 🎉
