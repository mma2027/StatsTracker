# StatsTracker Features

**Last Updated**: January 14, 2026

## Overview

StatsTracker is a comprehensive sports statistics tracking system designed for Haverford College Athletics. The system automatically fetches player statistics, tracks career progressions, detects milestone achievements, and sends automated notifications.

---

## Core Features

### 1. Automated Stats Fetching

**NCAA Stats Integration**
- Fetches stats from 10 Haverford NCAA teams
- Career statistics with season-by-season breakdown
- Automatic daily updates
- Generic parser works across all sports (14-33 stat categories per sport)
- Auto-recovery from invalid team IDs
- Selenium-based for JavaScript-rendered pages

**Supported Sports:**
- Men's Basketball
- Women's Basketball
- Men's Soccer
- Women's Soccer
- Men's Lacrosse
- Women's Lacrosse
- Baseball
- Softball
- Field Hockey
- Women's Volleyball

**Track & Field (TFRR Integration)**
- Athlete profile parsing
- Personal record tracking
- Meet results (in progress)
- Event-specific statistics

---

### 2. Database System

**SQLite Database**
- Flexible schema supports any sport/stat
- Career stats tracking (season-by-season)
- Historical data retention
- Fast search and filtering
- Automatic timestamp tracking

**Data Models:**
- **Players**: Name, sport, team, year
- **Stats**: Individual stat entries with timestamps
- **PlayerStats**: Aggregated career and recent stats
- Relationships and foreign keys for data integrity

**Features:**
- CRUD operations for all entities
- Efficient querying by sport, team, player
- Bulk updates for daily stats fetching
- Backup and export capabilities

---

### 3. Milestone Detection

**Configurable Thresholds**
- Per-sport milestone configuration
- Per-stat threshold values
- Custom proximity alerts (within X units)
- Multiple milestones per stat (e.g., 1000, 1500, 2000 points)

**Detection Features:**
- Proximity calculation (e.g., 990/1000 points)
- Historical milestone tracking
- Alert only for players with games scheduled
- Configurable alert windows

**Examples:**
- Basketball: 1000 career points, 500 rebounds
- Soccer: 20 career goals, 15 assists
- Volleyball: 500 kills, 1000 digs

---

### 4. Email Notifications

**HTML Email System**
- Beautiful responsive templates
- Professional design with Haverford branding
- Mobile-friendly layout

**Email Contents:**
- Game schedule for the day
- Players close to milestones
- Proximity to threshold (e.g., "John Doe: 990/1000 points")
- Sport and opponent information
- Always sends (even on days with no games/milestones)

**Configuration:**
- SMTP settings (Gmail, Outlook, etc.)
- Multiple recipients
- CC and BCC support
- Customizable send times

---

### 5. Gameday Checker

**Schedule Integration**
- Fetches from Haverford Athletics calendar API
- Fast single-request operation (~2-5 seconds)
- Full season schedule access
- Parses team, opponent, date, time, location

**Features:**
- Automatic game detection for milestone filtering
- Configurable lookahead period (default: 7 days)
- Works across all sports
- Timezone-aware

---

### 6. Web Interface

**Stats Browser**
- Browse all player statistics
- Organized by team/sport
- Player count and last updated info
- Direct links to detailed stats

**Global Player Search**
- Search across all sports and teams
- Real-time search with 300ms debounce
- Shows player name, sport, last updated
- Links to full stats view

**Individual Sport View**
- Complete stats table for all players
- Searchable and filterable
- Shows all stat categories
- Sortable columns
- Export-ready format

**Settings Page**
- Web-based configuration management
- Collapsible sections for better organization
- Real-time form validation
- Save confirmation

**Settings Sections:**
1. **Email Settings**
   - SMTP server and port
   - Sender email
   - Recipients (comma-separated)

2. **Notification Settings**
   - Enable/disable email notifications
   - Default proximity threshold
   - Note about per-stat customization

3. **Gameday Checker Settings**
   - Days to check ahead
   - Schedule refresh frequency

4. **Database Information** (read-only)
   - Database type
   - Database path
   - Storage location

5. **Milestone Configuration**
   - Per-sport configuration
   - Collapsible sport sections
   - Available stats dropdown (from database)
   - Individual threshold management
   - Per-stat proximity thresholds
   - Add/remove stats and thresholds dynamically

---

## Technical Features

### Performance
- Selenium with headless mode for NCAA fetching
- Efficient database queries with indexes
- Real-time search with debouncing
- Server-Sent Events for long operations
- CSS/JS minification in production

### Security
- YAML configuration (not in version control)
- Email password protection
- Input validation on all forms
- CSRF protection (Flask-WTF ready)
- SQL injection prevention (ORM)

### Reliability
- Comprehensive error handling
- Auto-recovery from failures
- Transaction-based database updates
- Logging at all levels
- Retry logic for network requests

### Testing
- 55+ unit tests
- Integration tests for database
- End-to-end tests for web interface
- GitHub Actions CI/CD pipeline
- Code coverage tracking

### Monitoring
- Detailed logging system
- Operation timestamps
- Success/failure tracking
- Email delivery confirmation
- Database update verification

---

## Workflow Integration

### Daily Automation (Planned)
1. **8 AM Daily Trigger** (cron job)
2. **Fetch Latest Stats** from NCAA for all teams
3. **Update Database** with new statistics
4. **Check Gameday Schedule** for upcoming games
5. **Detect Milestones** for players with games today
6. **Send Email** with alerts (or "no games today" message)

### Manual Operations
- Browse stats anytime via web interface
- Search for specific players
- Update milestone thresholds
- Configure email settings
- Export stats to CSV
- Test email sending

---

## Configuration Options

### Email Configuration
```yaml
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "stats@haverford.edu"
  sender_password: "app-password"
  recipients:
    - "sports-info@haverford.edu"
```

### Milestone Configuration
```yaml
milestones:
  mens_basketball:
    PTS:
      - 1000
      - 1500
      - 2000
    "Tot Reb":
      - 500
      - 750
    AST:
      - 300
      - 500
```

### Proximity Thresholds
```yaml
milestone_proximity:
  mens_basketball:
    PTS: 10    # Alert within 10 points
    AST: 5     # Alert within 5 assists
```

---

## User Roles & Access

Currently, the system is designed for:
- **Sports Information Directors**: Primary users who receive emails
- **Athletics Staff**: Web interface access for browsing stats
- **Coaches**: Stats viewing and milestone tracking
- **Media Relations**: Quick access to player achievements

Future enhancements could include:
- Role-based access control
- Public-facing stats portal
- Player/fan access with limited features

---

## Data Sources

### Current
- **NCAA Stats Website**: Primary source for 10 team sports
- **Haverford Athletics Calendar**: Game schedule data
- **TFRR**: Track & field statistics (partial)

### Planned
- **CricClubs**: Cricket statistics
- **Manual Entry**: For sports without digital sources
- **Historical Archives**: Past seasons and records

---

## Export & Integration

### CSV Export
- Export all stats to CSV files
- Organized by sport and team
- Timestamped filenames
- Available via scripts or web interface

### API (Planned)
- RESTful API for stats access
- JSON data format
- Authentication with API keys
- Rate limiting
- Public read-only endpoints

### Integration Points
- Could integrate with Haverford Athletics website
- Social media automation (auto-tweet milestones)
- SMS alerts for urgent milestones
- Mobile app data source

---

## Customization Options

### Per-Sport Customization
- Stat selection (choose which stats to track)
- Milestone thresholds (different for each sport)
- Proximity windows (tighter for rare achievements)
- Email formatting (sport-specific templates)

### Per-User Customization (Planned)
- Notification preferences
- Email frequency (daily, weekly, immediate)
- Sport subscriptions (only selected teams)
- Alert thresholds (personal preferences)

---

## Performance Metrics

### Current Performance
- **Stats Fetch**: 30-60 seconds per team (Selenium)
- **Database Update**: <1 second per player
- **Milestone Detection**: <1 second for all players
- **Email Send**: 2-3 seconds per email
- **Web Page Load**: <500ms for most pages
- **Search Response**: <100ms (debounced)

### Scalability
- Can handle 500+ players easily
- Database queries optimized with indexes
- Web interface uses pagination-ready design
- Could scale to multiple schools with minor changes

---

## Future Feature Ideas

### Short-term
- [ ] Historical stats visualization (charts)
- [ ] Player comparison tool
- [ ] Export to PDF
- [ ] Email preview in web interface

### Medium-term
- [ ] Mobile app
- [ ] Push notifications
- [ ] Social media integration
- [ ] Public stats portal

### Long-term
- [ ] Live game stat updates
- [ ] Real-time milestone tracking during games
- [ ] Recruiting metrics and analytics
- [ ] Alumni stats database
- [ ] Fan engagement features

---

## Known Limitations

### Current Limitations
- NCAA fetching requires Selenium (slower than API)
- Some team pages load slowly (2-5 second timeouts)
- TFRR integration incomplete
- No authentication/user management
- Single-school focus (Haverford only)

### Planned Improvements
- Caching for frequently accessed data
- Background task queue for long operations
- Mobile app for on-the-go access
- Multi-school support
- Advanced analytics and projections

---

## Documentation

- **README.md**: Project overview and quick start
- **TODO.md**: Current tasks and roadmap
- **FEATURES.md**: This file - comprehensive feature list
- **docs/guides/**: Detailed guides for specific features
- **docs/TEAM_GUIDE.md**: Collaboration and development guide
- **CONTRIBUTING.md**: How to contribute to the project

---

## Support & Feedback

For questions, bug reports, or feature requests:
- GitHub Issues: https://github.com/mma2027/StatsTracker/issues
- Email: [Your contact email]
- Documentation: See docs/ folder

---

## Version History

### v1.0 (Current)
- Complete NCAA stats fetching for 10 sports
- Database-driven stats storage
- Web interface with search and settings
- Milestone detection with custom thresholds
- Email notifications
- Gameday checker integration

### v0.5
- Initial prototype with basic fetching
- CSV-based storage
- Simple milestone detection

### Future Releases
- v1.1: Daily automation and TFRR completion
- v1.2: Enhanced web interface with charts
- v2.0: API and mobile app
