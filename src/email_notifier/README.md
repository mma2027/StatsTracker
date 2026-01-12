# Email Notifier Module

## Purpose
Sends formatted email notifications about milestone achievements and game schedules.

## Interface

### EmailNotifier Class

#### Methods

```python
def send_milestone_alert(
    self,
    proximities: List[MilestoneProximity],
    games: List[Game],
    date_for: date
) -> bool:
    """Send an email alert about milestones"""

def send_test_email(self) -> bool:
    """Send a test email to verify configuration"""

def validate_config(self) -> bool:
    """Validate email configuration"""

def add_recipient(self, email: str):
    """Add a recipient to the notification list"""

def remove_recipient(self, email: str):
    """Remove a recipient from the notification list"""
```

### EmailTemplate Class

Static methods for generating email content:
```python
@staticmethod
def generate_subject(date_for: date, num_games: int) -> str:
    """Generate email subject line"""

@staticmethod
def generate_milestone_email(
    proximities: List[MilestoneProximity],
    games: List[Game],
    date_for: date
) -> str:
    """Generate HTML email body"""

@staticmethod
def generate_text_version(
    proximities: List[MilestoneProximity],
    games: List[Game],
    date_for: date
) -> str:
    """Generate plain text email body"""
```

## Configuration

Email settings in `config/config.yaml`:

```yaml
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your-email@example.com"
  sender_password: "your-app-password"
  recipients:
    - "recipient1@example.com"
    - "recipient2@example.com"
```

### Gmail Setup

For Gmail, you need to:
1. Enable 2-factor authentication
2. Generate an app-specific password
3. Use the app password in the configuration

### Other Email Providers

The module works with any SMTP server:
- **Gmail**: smtp.gmail.com:587
- **Outlook**: smtp-mail.outlook.com:587
- **Yahoo**: smtp.mail.yahoo.com:587
- **Custom**: Your organization's SMTP server

## Email Format

The notifier sends multi-part emails with both HTML and plain text versions.

### HTML Email Features
- Styled with CSS for professional appearance
- Progress bars showing milestone completion
- Color-coded sections for games and milestones
- Haverford colors (maroon theme)
- Responsive design

### Plain Text Email
- Fallback for email clients that don't support HTML
- Well-formatted with ASCII separators
- All information from HTML version

## Implementation Tasks

- [x] Create email notifier class
- [x] Implement HTML email templates
- [x] Implement plain text templates
- [ ] Add email template customization
- [ ] Add attachment support (optional)
- [ ] Implement email scheduling
- [ ] Add unsubscribe functionality
- [ ] Create email preview/testing tool
- [ ] Add bounce handling
- [ ] Implement rate limiting

## Usage Examples

### Basic Usage
```python
from src.email_notifier import EmailNotifier
from datetime import date

email_config = {
    'smtp_server': 'smtp.gmail.com',
    'smtp_port': 587,
    'sender_email': 'sender@example.com',
    'sender_password': 'app-password',
    'recipients': ['recipient@example.com']
}

notifier = EmailNotifier(email_config)

# Validate configuration
if notifier.validate_config():
    # Send test email
    notifier.send_test_email()
```

### Send Milestone Alert
```python
# Assuming you have proximities and games from other modules
success = notifier.send_milestone_alert(
    proximities=close_milestones,
    games=todays_games,
    date_for=date.today()
)

if success:
    print("Alert sent successfully")
else:
    print("Failed to send alert")
```

### Manage Recipients
```python
notifier.add_recipient("newperson@example.com")
notifier.remove_recipient("oldperson@example.com")
```

## Security Considerations

1. **Never commit credentials**: Keep config files with passwords in .gitignore
2. **Use environment variables**: For production, use environment variables
3. **Use app passwords**: Don't use main account passwords
4. **TLS encryption**: Always use STARTTLS (port 587) or SSL (port 465)
5. **Validate recipients**: Implement email validation

## Troubleshooting

### Authentication Failed
- Check username and password
- For Gmail, use app-specific password
- Verify 2FA is enabled (for Gmail)

### Connection Timeout
- Check SMTP server and port
- Verify firewall isn't blocking outbound SMTP
- Try alternative ports (465 for SSL)

### Emails Going to Spam
- Set up SPF/DKIM records (if using custom domain)
- Avoid spam trigger words
- Keep email list clean
- Test with spam checkers

## Testing

Create tests in `tests/email_notifier/`:
- Test email generation
- Test template rendering
- Test with mock SMTP server
- Test error handling
- Test configuration validation

Use Python's `unittest.mock` to mock SMTP connections for testing.

## Integration Points

- **Used by**: Main orchestrator (to send notifications)
- **Uses**: Milestone detector output, Gameday checker output
- **Input**: MilestoneProximity and Game objects
- **Output**: Formatted email sent to recipients
