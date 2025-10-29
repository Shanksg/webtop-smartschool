# 🧪 SmartSchool Monitor - Testing Guide

## Quick Start Testing

### 1️⃣ **View Current Homework**
See what homework is currently being tracked:
```bash
python view_homework.py
```
**What it shows:**
- All tracked homework organized by date
- Token expiration status
- Number of assignments per student

---

### 2️⃣ **Test Monitor (No Changes)**
Run a single check without modifying state:
```bash
python test_monitor.py
```
**What happens:**
- Loads cached token
- Fetches current homework from API
- Compares with saved state
- Should show "Found X homework items" but NO "New homework detected"

---

### 3️⃣ **Test New Homework Detection**
Simulate finding new homework:
```bash
python test_new_homework.py
```
**What happens:**
- Clears the homework state
- Runs a fresh check
- All homework will be detected as "NEW"
- Perfect for testing notifications!

**Note:** After running this, run it again immediately to verify no duplicates are detected.

---

## 📋 Full Workflow Test

### Step-by-Step:

1. **Clear state and detect "new" homework:**
   ```bash
   python test_new_homework.py
   ```
   ✅ Should see: "New homework detected: ..." for each assignment

2. **Run again immediately (no new homework):**
   ```bash
   python test_monitor.py
   ```
   ✅ Should see: "Found X homework items" but NO "new" detections

3. **View what's tracked:**
   ```bash
   python view_homework.py
   ```
   ✅ Shows all homework organized by date

4. **Check logs for details:**
   ```bash
   tail -50 logs/smartschool-monitor.log
   ```

---

## 🔄 Test Token Expiration

Your token expires after ~23 hours. To test token renewal:

1. **Check token status:**
   ```bash
   python view_homework.py
   ```
   Look for "Token valid for X more hours"

2. **When token expires, manually extract new token:**
   ```bash
   python manual_token_extractor.py
   ```
   - Enter username: HHC129
   - Login in the browser that opens
   - Complete reCAPTCHA
   - Token will be cached automatically

3. **Verify new token works:**
   ```bash
   python test_monitor.py
   ```

---

## 🔔 Test Notifications (Optional)

If you set up notifications:

1. **Set notifier environment variable:**
   ```bash
   # Email example:
   export NOTIFIERS="mailto://user:password@smtp.gmail.com"

   # Or Telegram:
   export NOTIFIERS="tgram://bottoken/chatid"
   ```

2. **Test notification with new homework:**
   ```bash
   python test_new_homework.py
   ```
   ✅ Should receive notification with all 5 homework items

3. **Test no notification when no new homework:**
   ```bash
   python test_monitor.py
   ```
   ✅ Should NOT receive notification

---

## 🚀 Test Production Schedule

Run the monitor with the actual schedule (checks at 12:00, 16:00, 20:00):

```bash
python smartschool_monitor_v2.py
```

**How to stop:**
```bash
# Press Ctrl+C
# Or in another terminal:
pkill -f smartschool_monitor_v2.py
```

**Monitor logs in real-time:**
```bash
tail -f logs/smartschool-monitor.log
```

---

## 📁 Important Files

| File | Purpose |
|------|---------|
| `config/token_cache.json` | Cached authentication token |
| `config/homework_state.json` | Tracks which homework has been seen |
| `logs/smartschool-monitor.log` | Detailed logs of all operations |

---

## 🐛 Troubleshooting

### Token Invalid
**Error:** "Token is invalid or expired"
**Solution:**
```bash
python manual_token_extractor.py
```

### No Homework Found
**Check:**
1. Token is valid: `python view_homework.py`
2. Student params in config: `cat config/config.yaml`
3. API response in logs: `tail logs/smartschool-monitor.log`

### Duplicate Notifications
**Likely cause:** State file was deleted
**Solution:** Let the monitor run once to rebuild state

---

## ✅ Success Checklist

- [ ] Token extracted and cached
- [ ] `test_monitor.py` runs without errors
- [ ] `test_new_homework.py` detects all homework as new
- [ ] Running test twice shows no duplicates
- [ ] `view_homework.py` shows all current homework
- [ ] Logs show successful API calls
- [ ] Notifications working (if configured)

---

## 🎯 Next Steps

Once testing is complete:

1. **Run in production:**
   ```bash
   python smartschool_monitor_v2.py
   ```

2. **Set up as a service** (optional):
   - Linux: systemd service
   - macOS: launchd plist
   - Docker: Use the Dockerfile (if available)

3. **Monitor logs regularly:**
   ```bash
   tail -f logs/smartschool-monitor.log
   ```

4. **Remember to renew token every 23 hours**

---

**Questions?** Check the logs or re-run `python manual_token_extractor.py` if the token expires.
