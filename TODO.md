# StatsTracker TODO

**Last Updated**: January 14, 2026

## Current Status

StatsTracker is a **production-ready** system with database-driven stats tracking, web interface, and automated notifications. The system includes:

- ✅ 10 NCAA sports fetchers with career stats
- ✅ SQLite database with player statistics
- ✅ Web interface for browsing and searching stats
- ✅ Settings page for configuration management
- ✅ Automated milestone detection
- ✅ Email notifications with milestone alerts
- ✅ Gameday checker for schedule management

**Overall Completion**: ~95%

---

## High Priority Tasks

### 1. Complete Daily Automation Workflow
**Status**: In Progress (see plan file)

- [ ] Implement daily 8 AM automated workflow
  - [x] Stats fetching from all NCAA teams
  - [x] Gameday checker integration
  - [ ] Filter milestone checks by teams with games today
  - [ ] Always send email (even on empty days)
- [ ] Create cron job configuration
- [ ] Test empty-day email templates
- [ ] Set up log rotation and monitoring

**Files**: `main.py`, `src/email_notifier/templates.py`, `run_daily_check.sh`

---

### 2. TFRR (Track & Field) Integration
**Status**: Partial Implementation

- [x] Basic TFRR fetcher structure
- [x] Athlete profile page parsing
- [ ] Event results parsing improvements
- [ ] Meet results integration
- [ ] Testing with real Haverford track data

**Files**: `src/website_fetcher/tfrr_fetcher.py`, `scripts/fetch_tfrr_to_csv.py`

---

### 3. Additional Sports Fetchers
**Status**: Planned

- [ ] Cricket fetcher (CricClubs)
- [ ] Squash fetcher (if source available)
- [ ] Cross country fetcher (TFRR-based)

---

## Medium Priority Tasks

### 4. Web Interface Enhancements

- [x] Stats browser with search
- [x] Global player search
- [x] Settings configuration page
- [x] Per-sport milestone configuration
- [ ] Export stats to CSV from web interface
- [ ] Historical stats visualization (charts/graphs)
- [ ] Player profile pages with career progression
- [ ] Comparison tool (compare multiple players)

---

### 5. Milestone Detection Improvements

- [x] Basic milestone proximity detection
- [x] Per-stat proximity thresholds
- [ ] Advanced estimation algorithms (games remaining)
- [ ] Trend analysis (recent performance)
- [ ] Projection calculations (season-end stats)
- [ ] Multi-milestone tracking (approaching multiple at once)

---

### 6. Email Notification Enhancements

- [x] HTML email templates
- [x] Games schedule in emails
- [x] Milestone proximity alerts
- [ ] Weekly digest option
- [ ] Customizable email frequency per recipient
- [ ] Unsubscribe functionality
- [ ] Email preview in web interface

---

## Low Priority / Future Enhancements

### 7. API Development

- [ ] REST API for stats access
- [ ] API authentication
- [ ] Rate limiting
- [ ] API documentation (Swagger/OpenAPI)
- [ ] Public endpoints for read-only access

---

### 8. Mobile/Responsive Improvements

- [x] Basic responsive design
- [ ] Mobile-optimized navigation
- [ ] Progressive Web App (PWA) support
- [ ] Push notifications for milestones

---

### 9. Analytics & Reporting

- [ ] Dashboard with key metrics
- [ ] Season summary reports
- [ ] Milestone history tracking
- [ ] Performance analytics (team/player trends)
- [ ] Export reports to PDF

---

### 10. Deployment & DevOps

- [ ] Production server setup
- [ ] Automated backups (database)
- [ ] Monitoring and alerting
- [ ] Error tracking (Sentry integration)
- [ ] Performance monitoring
- [ ] Log aggregation

---

### 11. Testing & Quality

- [x] Unit tests for core modules (55+ tests)
- [x] GitHub Actions CI/CD
- [ ] End-to-end integration tests
- [ ] Performance/load testing
- [ ] Security audit
- [ ] Code coverage >90%

---

### 12. Documentation

- [x] README with overview
- [x] Module-specific documentation
- [x] Setup guides
- [ ] API documentation
- [ ] Deployment guide
- [ ] Troubleshooting guide
- [ ] User manual for web interface

---

## Completed Features ✅

### Core System
- ✅ NCAA stats fetcher (10 sports, career stats)
- ✅ Player database (SQLite with flexible schema)
- ✅ Milestone detector (basic proximity detection)
- ✅ Email notifier (HTML templates)
- ✅ Gameday checker (Haverford athletics calendar)

### Web Interface
- ✅ Stats browser with team/sport views
- ✅ Player search (global and per-sport)
- ✅ Settings page (email, milestones, notifications)
- ✅ Collapsible sections for better UX
- ✅ Per-sport stat selection (dropdowns)
- ✅ Individual threshold management

### Database Features
- ✅ Season-by-season career stats tracking
- ✅ Automatic schema updates
- ✅ Player statistics with timestamps
- ✅ Search and filtering capabilities

### Configuration
- ✅ YAML-based configuration
- ✅ Web-based settings editor
- ✅ Per-sport milestone thresholds
- ✅ Per-stat proximity thresholds
- ✅ Email settings management

---

## Known Issues

### High Priority
- None currently

### Medium Priority
- TFRR fetcher needs more robust error handling
- Some NCAA team pages load slowly (Selenium timeout issues)

### Low Priority
- Web interface could use loading indicators for long operations
- CSV export from web interface would be convenient

---

## Future Ideas / Brainstorming

- Integration with social media (auto-tweet milestones)
- SMS notifications for urgent milestones
- Alumni stats tracking (historical data)
- Recruiting metrics and analytics
- Integration with Haverford athletics website
- Fan-facing public stats portal
- Mobile app for coaches/staff
- Real-time game stat updates
- Live milestone tracking during games

---

## Development Workflow

### Adding a New Sport
1. Determine data source (NCAA, TFRR, etc.)
2. Create/update fetcher in `src/website_fetcher/`
3. Add sport to config.yaml milestones
4. Test fetching and database updates
5. Add milestone thresholds via web interface

### Making Database Changes
1. Update models in `src/player_database/models.py`
2. Create database migration if needed
3. Update queries in `database.py`
4. Test with existing data
5. Update relevant tests

### Adding Web Features
1. Update Flask route in `web/app.py`
2. Create/update Jinja2 template in `web/templates/`
3. Add CSS styles in `web/static/css/style.css`
4. Add JavaScript if needed in template or `web/static/js/`
5. Test in browser

---

## Notes

- Main orchestrator (`main.py`) ties all modules together
- Configuration is managed via `config/config.yaml` or web settings page
- Database is located at `data/stats.db`
- Logs are in `logs/` directory
- CSV exports go to `csv_exports/` directory

---

## Questions / Decisions Needed

- [ ] Should we support multiple seasons/years in database?
- [ ] What's the retention policy for old stats?
- [ ] Do we need user authentication for web interface?
- [ ] Should milestone emails go out immediately or on schedule?
- [ ] What's the backup strategy for production database?

---

## Resources

- [NCAA Stats Website](https://stats.ncaa.org)
- [TFRR Website](https://www.tfrrs.org)
- [Haverford Athletics](https://haverfordathletics.com)
- [GitHub Repository](https://github.com/mma2027/StatsTracker)
