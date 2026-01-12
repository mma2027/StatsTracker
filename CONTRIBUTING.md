# Contributing to StatsTracker

Thank you for contributing to StatsTracker! This guide will help you get started and work effectively with the team.

## Project Structure

StatsTracker is organized into independent modules:

- `gameday_checker/` - Checks for scheduled games
- `website_fetcher/` - Fetches stats from various sources
- `player_database/` - Manages player data storage
- `milestone_detector/` - Identifies milestone proximities
- `email_notifier/` - Sends email notifications

Each module can be developed independently with minimal conflicts.

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/mma2027/StatsTracker.git
cd StatsTracker
```

### 2. Set Up Your Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy configuration template
cp config/config.example.yaml config/config.yaml
```

### 3. Choose a Module to Work On

Each module has a README explaining:
- What it does
- What needs to be implemented
- Interface contracts
- Examples

See:
- `src/gameday_checker/README.md`
- `src/website_fetcher/README.md`
- `src/player_database/README.md`
- `src/milestone_detector/README.md`
- `src/email_notifier/README.md`

## Git Workflow

### Branch Naming Convention

Use descriptive branch names with prefixes:

- `feature/module-name-description` - New features
- `bugfix/module-name-description` - Bug fixes
- `docs/description` - Documentation updates
- `test/module-name-description` - Test additions

Examples:
```bash
feature/gameday-checker-scraper
feature/ncaa-fetcher-basketball
bugfix/database-connection-error
test/milestone-detector-calculations
```

### Workflow Steps

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Write code in your module directory
   - Follow the interface contracts
   - Write tests for your code

3. **Commit your changes**
   ```bash
   git add .
   git commit -m "Add feature: description of what you did"
   ```

4. **Push to GitHub**
   ```bash
   git push origin feature/your-feature-name
   ```

5. **Create a Pull Request**
   - Go to GitHub repository
   - Click "New Pull Request"
   - Select your branch
   - Fill in the PR template
   - Request review from team members

## Coding Standards

### Python Style

- Follow PEP 8 style guide
- Use type hints for function arguments and return values
- Write docstrings for all public functions and classes
- Keep functions small and focused

Example:
```python
def fetch_player_stats(player_id: str, sport: str) -> FetchResult:
    """
    Fetch statistics for a specific player.

    Args:
        player_id: Unique identifier for the player
        sport: Sport name (basketball, soccer, track, etc.)

    Returns:
        FetchResult object containing player statistics
    """
    pass
```

### Code Quality Tools

Before committing, run:

```bash
# Format code
black src/

# Check style
flake8 src/

# Type checking
mypy src/
```

### Testing

Write tests for your code:

```python
# tests/your_module/test_your_feature.py
import pytest
from src.your_module import YourClass

def test_your_function():
    """Test description"""
    result = YourClass().your_function()
    assert result == expected_value
```

Run tests:
```bash
# Run all tests
pytest

# Run tests for specific module
pytest tests/gameday_checker/

# Run with coverage
pytest --cov=src
```

## Module Independence

Each module should:

1. **Have clear interfaces** - Use the defined classes and methods
2. **Be testable independently** - Write unit tests with mocks
3. **Not depend on implementation details** - Only use public APIs
4. **Handle its own errors** - Don't let exceptions propagate

## Communication

### Before Starting Work

1. Check existing issues and PRs to avoid duplicate work
2. Comment on an issue you want to work on
3. If no issue exists, create one describing your plan

### Pull Request Guidelines

When creating a PR:

1. **Write a clear title**: "Add NCAA basketball stats fetcher"
2. **Describe what you did**: Explain the changes and why
3. **Reference issues**: "Closes #123" or "Related to #456"
4. **Add screenshots** (if UI changes)
5. **List testing done**: "Tested with mock data", "Added 10 unit tests"

### Code Review

When reviewing code:

- Be constructive and respectful
- Ask questions if something is unclear
- Suggest improvements, don't demand them
- Approve when code meets standards

When receiving feedback:

- Respond to all comments
- Ask for clarification if needed
- Make requested changes or explain why not
- Thank reviewers for their time

## Common Tasks

### Adding a New Data Source

1. Create `src/website_fetcher/your_source_fetcher.py`
2. Inherit from `BaseFetcher`
3. Implement required methods
4. Add to `src/website_fetcher/__init__.py`
5. Write tests
6. Update documentation

### Adding a New Sport

1. Update milestone configuration in `config/config.example.yaml`
2. Add sport-specific milestones to milestone detector
3. Update email templates if needed
4. Add sport to gameday checker if needed

### Running the System

```bash
# Normal operation (check and notify)
python main.py

# Update stats only (no notifications)
python main.py --update-stats

# Test email configuration
python main.py --test-email
```

## Handling Merge Conflicts

If you encounter merge conflicts:

1. **Update your branch**
   ```bash
   git fetch origin
   git rebase origin/main
   ```

2. **Resolve conflicts**
   - Open conflicted files
   - Edit to resolve conflicts
   - Remove conflict markers

3. **Continue rebase**
   ```bash
   git add .
   git rebase --continue
   ```

4. **Force push** (only to your feature branch!)
   ```bash
   git push -f origin feature/your-branch
   ```

## Questions?

- Open an issue for bugs or feature requests
- Use PR comments for code-specific questions
- Check module READMEs for implementation guidance

## License

By contributing, you agree that your contributions will be licensed under the same license as the project.
