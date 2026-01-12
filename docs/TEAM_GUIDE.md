# Team Development Guide

Quick reference for team members working on StatsTracker.

## Module Assignments

Assign team members to specific modules to avoid conflicts:

| Module | Owner | Status | Priority |
|--------|-------|--------|----------|
| Gameday Checker | TBD | Not Started | High |
| Website Fetcher - NCAA | TBD | Not Started | High |
| Website Fetcher - TFRR | TBD | Not Started | Medium |
| Player Database | TBD | Complete | - |
| Milestone Detector | TBD | Not Started | Medium |
| Email Notifier | TBD | Complete | - |

Update this table as team members volunteer for modules.

## Quick Start for Each Module

### Gameday Checker
**Goal**: Scrape Haverford athletics website for game schedules

**Files to modify**:
- `src/gameday_checker/checker.py` - Implement `_fetch_games()`

**What you need to do**:
1. Find Haverford athletics website URL for schedules
2. Use `requests` and `BeautifulSoup` to scrape schedule
3. Parse HTML to extract: team, opponent, date, time, location
4. Return list of `Game` objects
5. Handle errors gracefully

**Dependencies**: `requests`, `beautifulsoup4`

**Test with**:
```python
from src.gameday_checker import GamedayChecker
from datetime import date

checker = GamedayChecker("https://haverfordathletics.com/calendar")
games = checker.get_games_for_date(date(2024, 3, 15))
print(f"Found {len(games)} games")
```

### Website Fetcher - NCAA
**Goal**: Fetch player stats from NCAA website

**Files to modify**:
- `src/website_fetcher/ncaa_fetcher.py` - Implement all methods

**What you need to do**:
1. Study NCAA stats website structure
2. Implement `fetch_player_stats()` - get stats for a player ID
3. Implement `search_player()` - search for player by name
4. Parse HTML/JSON into standard format
5. Handle rate limiting and errors

**Output format**:
```python
{
    "player_id": "12345",
    "name": "John Doe",
    "sport": "basketball",
    "season": "2023-24",
    "stats": {
        "points": 450,
        "rebounds": 120,
        "assists": 80
    }
}
```

### Website Fetcher - TFRR
**Goal**: Fetch track & field stats from TFRR

**Files to modify**:
- `src/website_fetcher/tfrr_fetcher.py` - Implement all methods

**What you need to do**:
1. Study TFRR website structure (tfrrs.org)
2. Implement athlete stats fetching
3. Parse personal records (PRs) for events
4. Handle different event types (sprints, distance, field)
5. Return in standard format

**Special considerations**:
- Track events use times (need to handle formatting)
- Field events use distances/heights
- Need to track PRs specifically

### Milestone Detector Enhancements
**Goal**: Improve milestone detection logic

**Files to modify**:
- `src/milestone_detector/detector.py` - Enhance calculations

**What you need to do**:
1. Implement better `_estimate_games_to_milestone()`
2. Add sport-specific milestone logic
3. Handle different stat types (cumulative vs. averages vs. PRs)
4. Add trend analysis (is player trending up/down)
5. Improve proximity calculations

**Ideas to implement**:
- Track recent game performance
- Calculate moving averages
- Predict milestone achievement date
- Add confidence scores

### Email Template Improvements
**Goal**: Make emails look better

**Files to modify**:
- `src/email_notifier/templates.py` - Enhance HTML/CSS

**What you need to do**:
1. Improve HTML/CSS styling
2. Add Haverford branding/colors
3. Make responsive for mobile
4. Add player photos (optional)
5. Include charts/graphs (optional)

**Tools you can use**:
- Inline CSS (required for email)
- HTML tables for layout
- Keep it simple (email clients are limited)

## Git Workflow Cheat Sheet

### Starting Work
```bash
# Update your local repo
git pull origin main

# Create feature branch
git checkout -b feature/module-name-your-feature

# Make your changes...
```

### Committing Work
```bash
# See what changed
git status

# Stage your changes
git add src/your_module/

# Commit with good message
git commit -m "Implement NCAA stats fetching for basketball"

# Push to GitHub
git push origin feature/module-name-your-feature
```

### Creating Pull Request
1. Go to GitHub repository
2. Click "Pull requests" → "New pull request"
3. Select your branch
4. Fill in description:
   - What did you implement?
   - How did you test it?
   - Any issues or limitations?
5. Request review from teammate
6. Wait for approval and merge

### Updating Your Branch
```bash
# If main branch has updates
git checkout main
git pull origin main
git checkout feature/your-branch
git rebase main

# Fix any conflicts, then:
git push -f origin feature/your-branch
```

## Testing Your Module

### Unit Tests
Create tests in `tests/your_module/`:

```python
import pytest
from src.your_module import YourClass

def test_your_function():
    """Test description"""
    obj = YourClass()
    result = obj.your_function()
    assert result == expected_value
```

Run tests:
```bash
pytest tests/your_module/
```

### Integration Testing
Test with other modules:

```python
# Example: Test fetcher with database
from src.website_fetcher import NCAAFetcher
from src.player_database import PlayerDatabase

fetcher = NCAAFetcher()
db = PlayerDatabase("test.db")

result = fetcher.fetch_player_stats("12345", "basketball")
if result.success:
    # Add to database
    player = Player(...)
    db.add_player(player)
```

## Common Mistakes to Avoid

1. **Don't modify other modules** unless absolutely necessary
   - Stay in your module's directory
   - Only modify interface if you discuss with team first

2. **Don't commit config files with passwords**
   - `config/config.yaml` is in `.gitignore`
   - Use `config.example.yaml` for templates

3. **Don't commit large data files**
   - Database files are ignored
   - Don't check in scraped data

4. **Don't skip tests**
   - Write at least basic tests
   - Test error conditions too

5. **Don't merge your own PRs**
   - Always get review from teammate
   - Discuss any concerns

## Communication

### Before Starting Work
- Comment on GitHub issue: "I'll work on this"
- Coordinate with teammates to avoid duplication

### While Working
- Push commits regularly (don't wait weeks)
- Ask questions in issues or PRs
- Update team on progress

### Code Review
- Be respectful and constructive
- Ask questions: "Why did you choose...?"
- Suggest alternatives: "Have you considered...?"
- Approve when ready

## Module Dependencies

```
main.py
  ├── gameday_checker (independent)
  ├── website_fetcher (independent)
  ├── player_database (independent)
  ├── milestone_detector (needs: player_database)
  └── email_notifier (needs: milestone_detector, gameday_checker)
```

You can develop:
- Gameday checker independently
- Website fetcher independently
- Player database independently
- Milestone detector (after database is working)
- Email notifier (after detector and gameday checker work)

## Getting Help

### Technical Issues
- Check module README first
- Look at example code in tests
- Check `docs/interfaces.md` for contracts
- Ask in GitHub issues

### Git Issues
- Check `CONTRIBUTING.md`
- Ask teammate for help
- Can always create new branch and start over

### Design Questions
- Discuss in PR comments
- Create GitHub issue for discussion
- Check with module owner

## Progress Tracking

Update this checklist as you complete tasks:

### Gameday Checker
- [ ] Find Haverford athletics schedule page
- [ ] Implement HTML scraping
- [ ] Parse game data
- [ ] Handle multiple sports
- [ ] Write tests
- [ ] Document usage

### NCAA Fetcher
- [ ] Study NCAA website structure
- [ ] Implement player search
- [ ] Implement stats fetching for basketball
- [ ] Add soccer support
- [ ] Add other sports
- [ ] Write tests

### TFRR Fetcher
- [ ] Study TFRR website
- [ ] Implement athlete search
- [ ] Parse track event results
- [ ] Parse field event results
- [ ] Handle PRs correctly
- [ ] Write tests

### Milestone Detector
- [ ] Improve estimation algorithm
- [ ] Add sport-specific logic
- [ ] Add trend analysis
- [ ] Test with real data
- [ ] Optimize performance

### Email Templates
- [ ] Redesign HTML layout
- [ ] Add better CSS styling
- [ ] Test in multiple email clients
- [ ] Add mobile responsiveness
- [ ] Add optional features (photos, charts)

## Demo Day

When ready to demo:

1. **Prepare your data**
   ```bash
   # Add test players and stats
   python add_players.py
   python add_stats.py
   ```

2. **Test your module**
   ```bash
   pytest tests/your_module/ -v
   ```

3. **Run the system**
   ```bash
   python main.py
   ```

4. **Show the results**
   - Email received
   - Database content
   - Logs showing your module working

Good luck! 🚀
