# 🚀 Quick Start Guide - SmartSchool Monitor + Home Assistant

## 📍 You Are Here
Your current location: `/Users/shakedgofer/webtop_test/files`

---

## 🎯 Goal
Get homework notifications in Home Assistant in 5 steps!

---

## Step 1: Login & Get Token (2 minutes) 🔑

```bash
python manual_token_extractor.py
```

**What you'll see:**
1. Browser opens → SmartSchool login page
2. You enter: `HHC129` + password
3. Solve reCAPTCHA
4. ✅ Success message: "Token extracted and saved!"

**Result:** Token cached for 23 hours ✓

---

## Step 2: Setup Home Assistant Webhook (3 minutes) 🏠

### 2A. Edit Home Assistant Configuration

Open: `/config/configuration.yaml` in Home Assistant

Add this at the bottom:

```yaml
automation:
  - alias: "SmartSchool Homework Alert"
    trigger:
      - platform: webhook
        webhook_id: smartschool_homework
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

### 2B. Restart Home Assistant

Settings → System → Restart

**Your webhook URL is now:**
```
http://YOUR_HA_IP:8123/api/webhook/smartschool_homework
```

Example: `http://192.168.1.100:8123/api/webhook/smartschool_homework`

---

## Step 3: Connect Monitor to Home Assistant (1 minute) 🔗

**Replace `192.168.1.100` with YOUR Home Assistant IP:**

```bash
export NOTIFIERS="json://192.168.1.100:8123/api/webhook/smartschool_homework"
```

**Make it permanent:**

```bash
echo 'export NOTIFIERS="json://192.168.1.100:8123/api/webhook/smartschool_homework"' >> ~/.zshrc
source ~/.zshrc
```

---

## Step 4: Test It! (30 seconds) 🧪

```bash
python test_new_homework.py
```

**What happens:**
1. Monitor finds 5 homework items
2. Sends them to Home Assistant
3. 🎉 **You should see notification in Home Assistant!**

---

## Step 5: Run It! (Forever) 🚀

```bash
# Run in foreground (for testing)
python smartschool_monitor_v2.py

# OR run in background
nohup python smartschool_monitor_v2.py > monitor.log 2>&1 &
```

**What it does:**
- Checks for new homework at **12:00, 16:00, 20:00** daily
- Sends notification to Home Assistant when found
- Runs forever (until you stop it)

---

## 🛑 To Stop It

```bash
pkill -f smartschool_monitor_v2.py
```

---

## 🔄 Daily Maintenance

**Token expires every ~23 hours**

When you see "Token expired" error:
```bash
python manual_token_extractor.py
```

That's it! Login again, token cached for another 23 hours.

---

## 🧪 Useful Commands

```bash
# Check status & token validity
python view_homework.py

# Manual check (doesn't change state)
python test_monitor.py

# Simulate new homework (triggers notification)
python test_new_homework.py

# View logs
tail -20 logs/smartschool-monitor.log

# Check if monitor is running
ps aux | grep smartschool_monitor
```

---

## 📱 See It In Home Assistant

### Check Notifications:
1. Home Assistant → Notifications (bell icon)
2. Should see: "📚 SmartSchool Homework - גופר מעוז יוחנן"

### Check Persistent Notification:
1. Home Assistant → Sidebar
2. Look for notification card

---

## ⚡ Common Issues

### "Connection refused" to Home Assistant?
- Check Home Assistant IP address
- Make sure webhook is configured
- Restart Home Assistant

### "Token invalid"?
```bash
python manual_token_extractor.py
```

### Not receiving notifications?
```bash
# Test webhook manually:
curl -X POST http://192.168.1.100:8123/api/webhook/smartschool_homework \
  -H 'Content-Type: application/json' \
  -d '{"title":"Test","message":"Testing webhook"}'
```

### Where are the logs?
```bash
tail -f logs/smartschool-monitor.log
```

---

## 🎯 What Happens in Production?

```
12:00 → Monitor checks SmartSchool
      → New homework? → Send to Home Assistant ✓
      → No new homework? → Silent (no notification)

16:00 → (repeat)

20:00 → (repeat)

~23 hours later → Token expires
              → Run: python manual_token_extractor.py
```

---

## 📚 More Info

- **Detailed setup:** `cat HOME_ASSISTANT_SETUP.md`
- **Testing guide:** `cat TESTING_GUIDE.md`
- **All test scripts:** `ls test_*.py`

---

## ✅ Success Checklist

- [ ] Token extracted (`python manual_token_extractor.py`)
- [ ] Webhook added to Home Assistant
- [ ] Home Assistant restarted
- [ ] `NOTIFIERS` environment variable set
- [ ] Test worked (`python test_new_homework.py`)
- [ ] Received notification in Home Assistant
- [ ] Monitor running (`python smartschool_monitor_v2.py`)

**All checked?** 🎉 You're done!

---

## 🆘 Need Help?

1. Check logs: `tail logs/smartschool-monitor.log`
2. Test webhook: See "Common Issues" above
3. Verify token: `python view_homework.py`
4. Full docs: `cat HOME_ASSISTANT_SETUP.md`
