# SmartSchool Homework Monitor - Quick Start Guide

## 5-Minute Setup

### Step 1: Create Project Directory
```bash
mkdir smartschool-monitor
cd smartschool-monitor
# Copy all downloaded files here
```

### Step 2: Create Config File
Create a `config/config.yaml` file:

```bash
mkdir config
cat > config/config.yaml << EOF
students:
  - name: "Your Child's Name"
    username: "smartschool_username"
    password: "smartschool_password"
EOF
```

Replace with actual SmartSchool login credentials.

### Step 3: Get Home Assistant Token (if using)
1. Open Home Assistant
2. Click your profile (bottom left)
3. Scroll down → "Long-Lived Access Tokens"
4. Click "Create Token"
5. Name it "SmartSchool Monitor"
6. Copy the token

### Step 4: Configure docker-compose.yml
Edit `docker-compose.yml` and update the `NOTIFIERS` line:

**For Home Assistant:**
```yaml
NOTIFIERS: "hassio://user@192.168.1.100/YOUR_TOKEN_HERE"
```

**For Telegram (get bot token and chat ID first):**
```yaml
NOTIFIERS: "tgram://your_bot_token/your_chat_id"
```

**For Discord (get webhook URL):**
```yaml
NOTIFIERS: "discord://avatar@webhook_id/webhook_token"
```

**Multiple services (comma-separated):**
```yaml
NOTIFIERS: "hassio://user@192.168.1.100/token,tgram://token/chatid"
```

### Step 5: Customize Check Times (Optional)
Default times are 12:00, 16:00, 20:00. To change:

```yaml
SCHEDULES: "08:00,12:00,16:00,20:00"
```

### Step 6: Start the Service
```bash
docker-compose up -d
```

Check if it's running:
```bash
docker-compose logs -f smartschool-monitor
```

You should see:
```
Starting SmartSchool Homework Monitor
Loaded 1 students from config
Scheduled check at 12:00
Scheduled check at 16:00
Scheduled check at 20:00
```

### Step 7: Wait for First Check
The service checks at your configured times. Logs will show if new homework is detected and notifications sent.

## Troubleshooting

**Container won't start:**
```bash
docker-compose logs smartschool-monitor
```

**Check if credentials are correct:**
Try logging into SmartSchool manually with the same credentials.

**Not sending notifications:**
1. Verify `NOTIFIERS` is set in `docker-compose.yml`
2. Check logs for notification errors
3. Test the service URL is correct

**Stop the service:**
```bash
docker-compose down
```

**View detailed logs:**
```bash
docker-compose logs --tail 50 smartschool-monitor
```

## File Structure After Setup
```
smartschool-monitor/
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── smartschool_monitor.py
├── config/
│   └── config.yaml              (your credentials)
└── logs/                        (auto-created)
    └── smartschool-monitor.log
```

## Next Steps

- See **README.md** for detailed documentation
- Customize notification services (Discord, Telegram, Email, etc.)
- Add multiple students to monitor
- Adjust check times to your schedule

## Common Notification URLs

**Home Assistant:**
```
hassio://user@YOUR_IP/YOUR_TOKEN
```

**Telegram:**
```
tgram://BOT_TOKEN/CHAT_ID
```

**Discord:**
```
discord://WEBHOOK_ID/WEBHOOK_TOKEN
```

**Email (Gmail):**
```
mailto://your_email:app_password@gmail.com/recipient@example.com
```

For more services, see: https://github.com/caronc/apprise/wiki

## Support

See README.md for detailed troubleshooting guide.
