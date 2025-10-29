# 🏠 MQTT Setup for Home Assistant Entity Tracking

## Overview

This guide shows you how to set up MQTT to create **persistent entities** in Home Assistant that track homework in real-time.

**What you get:**
- `sensor.smartschool_homework_count` - Number of homework items for today
- `sensor.smartschool_homework_details` - Full homework text
- `sensor.smartschool_last_check` - When homework was last checked

---

## Prerequisites

### 1. Install MQTT Broker in Home Assistant

**Via Home Assistant UI:**
1. Settings → Add-ons → Add-on Store
2. Search for "Mosquitto broker"
3. Click Install
4. After installation:
   - Click Configuration tab
   - Leave default settings (or add username/password if desired)
   - Click Start
   - Enable "Start on boot"

**Verify it's running:**
- Should show "Running" with a green indicator

---

### 2. Enable MQTT Integration in Home Assistant

1. Settings → Devices & Services → Add Integration
2. Search for "MQTT"
3. Click on MQTT
4. Enter broker details:
   - **Broker**: `localhost` (or `192.168.88.200` if accessing from another machine)
   - **Port**: `1883`
   - **Username**: (leave empty if you didn't set one)
   - **Password**: (leave empty if you didn't set one)
5. Click Submit

---

## Setup SmartSchool Monitor with MQTT

### Step 1: Install MQTT Python Library

```bash
pip install paho-mqtt
```

### Step 2: Configure MQTT Environment Variables

```bash
# Required - Your Home Assistant IP where MQTT broker runs
export MQTT_BROKER="192.168.88.200"

# Optional - Port (default: 1883)
export MQTT_PORT="1883"

# Optional - Username/Password (if you configured them)
export MQTT_USER=""
export MQTT_PASS=""

# Keep your webhook for notifications
export NOTIFIERS="json://192.168.88.200:8123/api/webhook/smartschool_homework"
```

**Make it permanent:**

```bash
cat >> ~/.zshrc <<'EOF'
# SmartSchool Monitor - MQTT
export MQTT_BROKER="192.168.88.200"
export MQTT_PORT="1883"
export NOTIFIERS="json://192.168.88.200:8123/api/webhook/smartschool_homework"
EOF

source ~/.zshrc
```

---

### Step 3: Test It!

```bash
python test_new_homework.py
```

**Expected output:**
```
✓ MQTT connected successfully
Published MQTT discovery for גופר מעוז יוחנן
Published MQTT state for גופר מעוז יוחנן: 3 homework items
```

---

## Verify in Home Assistant

### Check the Entities Were Created

1. Settings → Devices & Services → MQTT
2. Click on "SmartSchool - גופר מעוז יוחנן" device
3. You should see 3 entities:
   - **Homework Count** (e.g., "3 assignments")
   - **Homework Details** (full text)
   - **Last Check** (timestamp)

### View in Dashboard

Go to Overview dashboard - the entities are now available!

---

## Create Dashboard Card

Add this to your Lovelace dashboard:

```yaml
type: vertical-stack
cards:
  # Homework Count Card
  - type: entity
    entity: sensor.smartschool_homework_count
    name: "📚 Today's Homework"
    icon: mdi:book-open-variant

  # Homework Details Card
  - type: markdown
    content: |
      {{ states('sensor.smartschool_homework_details') }}

  # Last Updated
  - type: entity
    entity: sensor.smartschool_last_check
    name: Last Checked
    icon: mdi:clock-check
```

**Or use the UI:**

1. Edit Dashboard → Add Card
2. Choose "Entity" card
3. Select `sensor.smartschool_homework_count`
4. Repeat for details and last check

---

## Advanced: Automations Using the Entities

### Example 1: Notify When Homework Count Changes

```yaml
automation:
  - alias: "SmartSchool - Homework Count Changed"
    trigger:
      - platform: state
        entity_id: sensor.smartschool_homework_count
    condition:
      - condition: template
        value_template: "{{ states('sensor.smartschool_homework_count') | int > 0 }}"
    action:
      - service: notify.mobile_app_your_phone
        data:
          title: "📚 Homework Update"
          message: "{{ states('sensor.smartschool_homework_count') }} assignments for today"
```

### Example 2: Turn on Light When Homework > 0

```yaml
automation:
  - alias: "SmartSchool - Homework Reminder Light"
    trigger:
      - platform: state
        entity_id: sensor.smartschool_homework_count
    condition:
      - condition: template
        value_template: "{{ states('sensor.smartschool_homework_count') | int > 0 }}"
      - condition: time
        after: "16:00:00"
        before: "20:00:00"
    action:
      - service: light.turn_on
        target:
          entity_id: light.desk_lamp
        data:
          brightness: 255
          color_name: blue
```

### Example 3: TTS Announcement at 4 PM if Homework Exists

```yaml
automation:
  - alias: "SmartSchool - Homework Reminder TTS"
    trigger:
      - platform: time
        at: "16:00:00"
    condition:
      - condition: template
        value_template: "{{ states('sensor.smartschool_homework_count') | int > 0 }}"
    action:
      - service: tts.google_translate_say
        target:
          entity_id: media_player.living_room_speaker
        data:
          message: >
            יש {{ states('sensor.smartschool_homework_count') }} שיעורי בית להיום
```

---

## How It Works

### Auto-Discovery

When the monitor runs for the first time, it publishes MQTT discovery messages to:
```
homeassistant/sensor/smartschool_[student]/config
```

Home Assistant automatically creates the entities!

### State Updates

Every time the monitor checks for homework, it publishes:
- **Count**: Number of homework items for today
- **Details**: Full formatted homework text
- **Last Check**: ISO timestamp of last check

### Persistence

MQTT messages are published with `retain=True`, so the entities persist even if you restart Home Assistant.

---

## Troubleshooting

### "MQTT not configured" in logs

**Check:**
```bash
echo $MQTT_BROKER
```

Should show your HA IP. If empty:
```bash
export MQTT_BROKER="192.168.88.200"
```

### "paho-mqtt not installed" warning

```bash
pip install paho-mqtt
```

### Entities not appearing in Home Assistant

**Check MQTT integration is enabled:**
1. Settings → Devices & Services
2. Should see "MQTT" integration

**Check MQTT broker is running:**
1. Settings → Add-ons → Mosquitto broker
2. Should show "Running"

**Check logs:**
```bash
tail -20 logs/smartschool-monitor.log | grep MQTT
```

Should see:
```
✓ MQTT connected successfully
Published MQTT discovery for [student name]
```

### Test MQTT manually

**Subscribe to topics:**
```bash
# Install mosquitto clients
brew install mosquitto  # macOS
# or
sudo apt install mosquitto-clients  # Linux

# Subscribe to all SmartSchool topics
mosquitto_sub -h 192.168.88.200 -t "smartschool/#" -v
```

**Publish test message:**
```bash
mosquitto_pub -h 192.168.88.200 -t "smartschool/test" -m "Hello"
```

---

## What's the Difference: MQTT vs Webhook?

| Feature | MQTT Entities | Webhook Notifications |
|---------|--------------|----------------------|
| **Purpose** | Persistent state tracking | One-time notifications |
| **When updates** | Every check (12:00, 16:00, 20:00) | Only when NEW homework |
| **Home Assistant** | Creates entities/sensors | Triggers automation |
| **Dashboard** | Can display in cards | Cannot display |
| **Automations** | Can use in triggers/conditions | Only in triggered action |
| **History** | Full history graph | No history |

**Recommendation:** Use **BOTH**
- MQTT for tracking and dashboard
- Webhook for instant notifications

---

## Complete Example Setup

### Environment Variables
```bash
export MQTT_BROKER="192.168.88.200"
export MQTT_PORT="1883"
export NOTIFIERS="json://192.168.88.200:8123/api/webhook/smartschool_homework"
```

### Home Assistant Configuration

**Dashboard Card:**
```yaml
type: vertical-stack
title: "📚 SmartSchool Homework"
cards:
  - type: glance
    entities:
      - entity: sensor.smartschool_homework_count
        name: Today's Homework
      - entity: sensor.smartschool_last_check
        name: Last Updated

  - type: markdown
    content: |
      {{ states('sensor.smartschool_homework_details') }}

  - type: conditional
    conditions:
      - entity: sensor.smartschool_homework_count
        state_not: "0"
    card:
      type: button
      name: "Mark as Done"
      icon: mdi:checkbox-marked-circle
      tap_action:
        action: call-service
        service: input_boolean.toggle
        service_data:
          entity_id: input_boolean.homework_done
```

---

## Testing Checklist

- [ ] Mosquitto broker installed and running
- [ ] MQTT integration added in HA
- [ ] `pip install paho-mqtt` completed
- [ ] `MQTT_BROKER` environment variable set
- [ ] Ran `python test_new_homework.py`
- [ ] Saw "MQTT connected successfully" in logs
- [ ] Entities appear in Settings → Devices & Services → MQTT
- [ ] Can see entities in Developer Tools → States
- [ ] Dashboard card shows homework count
- [ ] Entities update when running test again

---

## Summary

**To enable MQTT entities:**

```bash
# 1. Install MQTT library
pip install paho-mqtt

# 2. Set environment variable
export MQTT_BROKER="192.168.88.200"

# 3. Test it
python test_new_homework.py

# 4. Check Home Assistant → Settings → Devices & Services → MQTT
```

**You get 3 auto-created entities:**
- 📊 Homework Count
- 📝 Homework Details
- 🕐 Last Check

**Use in dashboard, automations, and scripts!**
