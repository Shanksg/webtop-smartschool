# SmartSchool Monitor - Environment Variables Reference

# This file documents all environment variables used by the service
# Edit docker-compose.yml to change these values

## SCHEDULES
# Format: HH:MM,HH:MM,HH:MM (24-hour format, comma-separated)
# When to check for homework each day
# Default: 12:00,16:00,20:00
# Examples:
#   SCHEDULES=08:00,12:00,16:00,20:00,22:00
#   SCHEDULES=09:00,14:00,18:00
#   SCHEDULES=12:00
SCHEDULES="12:00,16:00,20:00"

## NOTIFIERS
# Apprise notification URLs (comma-separated for multiple services)
# Default: (empty - no notifications)
# 
# FORMAT: service://parameters
# 
# EXAMPLES:
#
# Home Assistant:
#   NOTIFIERS="hassio://user@192.168.1.100/your_long_lived_access_token"
#   
# Telegram:
#   NOTIFIERS="tgram://BOT_TOKEN/CHAT_ID"
#   
# Discord:
#   NOTIFIERS="discord://WEBHOOK_ID/WEBHOOK_TOKEN"
#   
# Email (Gmail):
#   NOTIFIERS="mailto://your_email:app_password@gmail.com/recipient@example.com"
#   
# Slack:
#   NOTIFIERS="slack://TOKEN/CHANNEL"
#
# Multiple services (comma-separated):
#   NOTIFIERS="hassio://user@192.168.1.100/token,tgram://bottoken/chatid"
#
NOTIFIERS="hassio://user@192.168.1.100/YOUR_ACCESS_TOKEN"

## PYTHONUNBUFFERED
# Ensure Python output is sent immediately (don't buffer)
# Should be "1" - helps with logging
PYTHONUNBUFFERED="1"

## Optional: LOG_LEVEL (not currently used, but can be added)
# DEBUG - Very detailed logs
# INFO - Normal logs (default)
# WARNING - Only warnings and errors
# ERROR - Only errors
# LOG_LEVEL="INFO"

---

## HOW TO GET TOKENS/IDS

### Home Assistant Access Token
1. Go to Home Assistant web interface
2. Click your profile icon (bottom left)
3. Scroll down to "Long-Lived Access Tokens"
4. Click "Create Token"
5. Name it "SmartSchool Monitor"
6. Copy the token
7. Use in NOTIFIERS: hassio://user@YOUR_HA_IP/TOKEN

### Telegram Bot Token & Chat ID
1. Message @BotFather on Telegram
2. Create a new bot: /newbot
3. Save the bot token
4. Message your bot something
5. Get your Chat ID: https://api.telegram.org/botTOKEN/getUpdates
6. Find the chat ID in the JSON response
7. Use in NOTIFIERS: tgram://bottoken/chatid

### Discord Webhook
1. Open Discord server
2. Go to channel settings → Integrations
3. Create Webhook
4. Copy the Webhook URL
5. Extract WEBHOOK_ID and WEBHOOK_TOKEN from URL:
   https://discordapp.com/api/webhooks/WEBHOOK_ID/WEBHOOK_TOKEN
6. Use in NOTIFIERS: discord://WEBHOOK_ID/WEBHOOK_TOKEN

### Gmail App Password
1. Go to myaccount.google.com
2. Security → 2-Step Verification (must be enabled)
3. App passwords
4. Select Mail & Windows Computer
5. Copy the password
6. Use in NOTIFIERS: mailto://your_email:app_password@gmail.com/recipient@example.com

---

## EDITING docker-compose.yml

In docker-compose.yml, find the "environment:" section and modify:

```yaml
services:
  smartschool-monitor:
    environment:
      SCHEDULES: "12:00,16:00,20:00"
      NOTIFIERS: "hassio://user@192.168.1.100/token"
      PYTHONUNBUFFERED: "1"
```

After editing, run:
```bash
docker-compose up -d --build
```

---

## VERIFICATION

After setting environment variables:

```bash
# Check if environment variables are set
docker-compose exec smartschool-monitor env | grep -E 'SCHEDULES|NOTIFIERS'

# View service logs to see what's configured
docker-compose logs smartschool-monitor | grep -E 'Scheduled|notifier'
```

You should see output like:
```
Scheduled check at 12:00
Scheduled check at 16:00
Scheduled check at 20:00
Added notifier: hassio://user@...
```

---

## TROUBLESHOOTING

**Notifiers not working?**
- Verify NOTIFIERS is set: `docker-compose config | grep NOTIFIERS`
- Check URL format matches examples above
- View logs: `docker-compose logs smartschool-monitor | grep -i notif`

**Wrong check times?**
- Verify SCHEDULES is set: `docker-compose config | grep SCHEDULES`
- Restart service: `docker-compose restart`
- Check logs for scheduled times

**Need to change variables?**
- Edit docker-compose.yml
- Run: `docker-compose up -d --build`
- Verify: `docker-compose logs smartschool-monitor`
