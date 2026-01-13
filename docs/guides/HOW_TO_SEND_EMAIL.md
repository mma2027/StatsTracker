# How to Send the Notification Email

## Email Preview
The notification email has been configured to send to: **hzhang3@haverford.edu**

Preview the HTML design: `email_preview.html` (open in browser)

## To Actually Send Emails

You need to configure SMTP credentials. Here are your options:

### Option 1: Use Gmail (Recommended)

#### Step 1: Get Gmail App Password

1. Go to your Google Account: https://myaccount.google.com/
2. Select **Security** from the left menu
3. Under "How you sign in to Google", enable **2-Step Verification** (if not already enabled)
4. Go back to Security, find **App passwords**
5. Create a new app password:
   - App: Mail
   - Device: Other (enter "StatsTracker")
6. Google will generate a 16-character password like `xxxx xxxx xxxx xxxx`
7. **Copy this password** (you won't see it again!)

#### Step 2: Update Configuration

Edit `config/config.yaml`:

```yaml
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "YOUR_GMAIL@gmail.com"  # Your Gmail address
  sender_password: "xxxx xxxx xxxx xxxx"  # The app password from step 1
  recipients:
    - "hzhang3@haverford.edu"
```

### Option 2: Use Haverford Email

If you have access to Haverford's SMTP server, ask IT for:
- SMTP server address
- SMTP port
- Authentication requirements

Then update config.yaml accordingly.

## Testing

### Test 1: Validate Configuration
```bash
./venv/bin/python main.py --test-email
```

This will:
- Check if your config is valid
- Send a test email
- Confirm delivery

### Test 2: Send Notification for Jan 14

Create a script to simulate Jan 14:

```bash
./venv/bin/python << 'EOF'
from datetime import date
from src.gameday_checker.models import Game, Team
from src.player_database import PlayerDatabase
from src.milestone_detector import MilestoneDetector
from src.email_notifier import EmailNotifier
import yaml

# Load config
with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

# Setup
check_date = date(2026, 1, 14)

# Create games manually
games = [
    Game(
        team=Team(name="Haverford Women's Basketball", sport="Women's Basketball"),
        opponent="Ursinus",
        date=check_date,
        location="home",
        time="7:00 PM"
    ),
    Game(
        team=Team(name="Haverford Men's Basketball", sport="Men's Basketball"),
        opponent="Ursinus",
        date=check_date,
        location="home",
        time="5:00 PM"
    )
]

# Get milestones
db = PlayerDatabase('data/stats.db')
milestones = config.get('milestones', {})
detector = MilestoneDetector(db, milestones)
all_proximities = detector.check_all_players_milestones(proximity_threshold=20)

# Filter individual players only
proximities_list = []
for player_id, prox_list in all_proximities.items():
    for prox in prox_list:
        if 'Total' not in prox.player_name and 'Opponent' not in prox.player_name:
            proximities_list.append(prox)

# Sort by distance
proximities_list.sort(key=lambda p: abs(p.distance))

# Send email
notifier = EmailNotifier(config.get('email', {}))
if notifier.validate_config():
    print(f"Sending email to {config['email']['recipients']}")
    print(f"Games: {len(games)}")
    print(f"Milestone alerts: {len(proximities_list[:10])}")

    success = notifier.send_milestone_alert(
        proximities=proximities_list[:10],
        games=games,
        date_for=check_date
    )

    if success:
        print("✅ Email sent successfully!")
    else:
        print("❌ Failed to send email")
else:
    print("❌ Email configuration is invalid")
    print("Please update config/config.yaml with SMTP credentials")
EOF
```

## Current Configuration Status

✅ Recipient configured: hzhang3@haverford.edu
❌ SMTP password needed: Update `sender_password` in config.yaml
✅ Email template ready: email_preview.html
✅ Database populated: 136 players with stats
✅ Milestone detection working: 10+ alerts ready

## Quick Start (After Configuring SMTP)

Once you have SMTP credentials configured:

```bash
# Test email works
./venv/bin/python main.py --test-email

# Run full orchestrator (will check for today's games)
./venv/bin/python main.py

# Enable auto-update for production
# Edit config.yaml: auto_update_stats: true
# Set up daily cron job at 8 AM:
# 0 8 * * * cd /path/to/StatsTracker && ./venv/bin/python main.py
```

## What Gets Sent

The email includes:
- **Haverford College branding** (maroon #8B0000)
- **Games section**: All games scheduled for the date
  - Sport, teams, opponent, location (Home/Away), time
- **Milestone alerts section**: Top 10 players approaching milestones
  - Player name, sport, stat details
  - Current value, target milestone, distance remaining
  - Visual progress bar showing percentage complete
  - Estimated games to milestone (if available)
- **Professional footer** with StatsTracker branding

## Email Preview Details

Open `email_preview.html` in your browser to see:
- Full HTML design with Haverford colors
- Responsive layout
- Progress bars for each milestone
- Clean, professional formatting

## Need Help?

If you encounter issues:
1. Check that 2-Step Verification is enabled on Google
2. Verify the app password was copied correctly (no spaces)
3. Make sure sender_email matches the Gmail account that generated the app password
4. Try the test email command first before full notifications
