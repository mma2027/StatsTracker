# 📧 Email Notification Setup Summary

## What's Been Configured

✅ **Recipient Email**: hzhang3@haverford.edu
✅ **Test Date**: January 14, 2026 (2 basketball games vs Ursinus)
✅ **Database**: 136 players with stats ready
✅ **Milestone Detection**: Configured for basketball milestones
✅ **Email Template**: Professional HTML design with Haverford branding
✅ **Preview Generated**: email_preview.html

## What the Notification Will Include

### Games on January 14, 2026:
- 🏀 **Women's Basketball** vs Ursinus (Home, 7:00 PM)
- 🏀 **Men's Basketball** vs Ursinus (Home, 5:00 PM)

### Milestone Alerts (Sample):
- **Audrey Jakway** (Women's Basketball): 196/200 PTS (4 away)
- **Shae Mercer** (Women's Basketball): 101/100 PTS (✓ ACHIEVED!)
- **Tyler Nolan** (Men's Basketball): 112/100 PTS (✓ ACHIEVED!)
- **Bri Heafey** (Women's Basketball): 87/100 PTS (13 away)
- ...and more!

## 🚀 Quick Start: Send the Email

### Step 1: Get Gmail App Password

1. Go to https://myaccount.google.com/security
2. Enable **2-Step Verification** (if not already)
3. Click **App passwords**
4. Create password for "Mail" → "Other (StatsTracker)"
5. Copy the 16-character password

### Step 2: Update Configuration

Edit `config/config.yaml` line 8-9:

```yaml
sender_email: "YOUR_EMAIL@gmail.com"  # Your Gmail address
sender_password: "xxxx xxxx xxxx xxxx"  # Paste app password here
```

### Step 3: Send Test Email

```bash
cd /home/hongyi/StatsTracker
./venv/bin/python main.py --test-email
```

### Step 4: Send Jan 14 Notification

```bash
./venv/bin/python send_jan14_notification.py
```

This will:
1. Show you the games and milestone alerts
2. Ask for confirmation
3. Send the email to hzhang3@haverford.edu

## 📊 Preview the Email Design

Open in your browser:
```bash
firefox email_preview.html
# or
google-chrome email_preview.html
# or
open email_preview.html  # macOS
```

The email includes:
- **Haverford maroon branding** (#8B0000)
- **Games section** with times and locations
- **Milestone alerts** with progress bars
- **Professional formatting**

## 🔧 Troubleshooting

**Email not sending?**
- Make sure 2-Step Verification is enabled on your Google account
- Verify the app password has no spaces when pasted
- Confirm sender_email matches the Gmail that created the app password

**Need more help?**
See `HOW_TO_SEND_EMAIL.md` for detailed instructions

## 📁 Files Created

- `email_preview.html` - Visual preview of email design
- `send_jan14_notification.py` - Script to send Jan 14 notification
- `HOW_TO_SEND_EMAIL.md` - Detailed setup instructions
- `config/config.yaml` - Updated with your email (needs SMTP password)

## 🎯 What Happens Next

Once SMTP is configured, the full workflow works:

```bash
# Manual notification for any date
./venv/bin/python main.py

# Or automate daily at 8 AM with cron:
0 8 * * * ./venv/bin/python main.py
```

With `auto_update_stats: true` in config, it will:
1. Fetch latest stats from NCAA automatically
2. Check today's games
3. Detect milestone proximities
4. Send email if there are games or milestones

---

**Ready to send?** Update the SMTP password and run:
```bash
./venv/bin/python send_jan14_notification.py
```
