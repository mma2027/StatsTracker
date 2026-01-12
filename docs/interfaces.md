# Module Interfaces

This document defines the interfaces between modules. Follow these contracts to ensure modules work together correctly.

## Gameday Checker → Main Orchestrator

### Output: List[Game]

```python
@dataclass
class Game:
    team: Team
    opponent: str
    date: datetime
    location: str
    time: Optional[str]
```

### Methods Used
- `get_games_for_today() -> List[Game]`
- `get_games_for_date(check_date: date) -> List[Game]`

## Website Fetcher → Player Database

### Output: FetchResult

```python
@dataclass
class FetchResult:
    success: bool
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    timestamp: datetime
    source: str
```

### Data Format
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

### Methods Used by Database
- `fetch_player_stats(player_id: str, sport: str) -> FetchResult`
- `fetch_team_stats(team_id: str, sport: str) -> FetchResult`
- `search_player(name: str, sport: str) -> FetchResult`

## Player Database → Milestone Detector

### Output: PlayerStats

```python
@dataclass
class PlayerStats:
    player: Player
    career_stats: Dict[str, Any]
    season_stats: Dict[str, Dict[str, Any]]
    recent_entries: List[StatEntry]
```

### Methods Used by Detector
- `get_player_stats(player_id: str, season: Optional[str]) -> Optional[PlayerStats]`
- `get_all_players(sport: Optional[str], active_only: bool) -> List[Player]`

## Milestone Detector → Email Notifier

### Output: MilestoneProximity

```python
@dataclass
class MilestoneProximity:
    player_id: str
    player_name: str
    milestone: Milestone
    current_value: Any
    distance: Any
    percentage: float
    estimated_games_to_milestone: Optional[int]
```

### Methods Used by Notifier
- `check_all_players_milestones(sport: Optional[str], proximity_threshold: int) -> Dict[str, List[MilestoneProximity]]`
- `get_priority_alerts(sport: Optional[str]) -> List[MilestoneProximity]`

## Email Notifier → External

### Input: MilestoneProximity + Game

### Output: Email sent to recipients

### Methods Used by Orchestrator
- `send_milestone_alert(proximities: List[MilestoneProximity], games: List[Game], date_for: date) -> bool`
- `validate_config() -> bool`

## Data Flow

```
┌─────────────────┐
│  Gameday        │
│  Checker        │──────┐
└─────────────────┘      │
                         │
┌─────────────────┐      │     ┌─────────────────┐
│  Website        │      │     │  Milestone      │
│  Fetcher        │──────┼────>│  Detector       │
└─────────────────┘      │     └─────────────────┘
                         │              │
┌─────────────────┐      │              │
│  Player         │      │              │
│  Database       │──────┘              │
└─────────────────┘                     │
                                        │
                                        v
                              ┌─────────────────┐
                              │  Email          │
                              │  Notifier       │
                              └─────────────────┘
                                        │
                                        v
                                  Recipients
```

## Configuration Interface

All modules receive configuration from `config/config.yaml`:

### Gameday Checker
```yaml
gameday:
  haverford_schedule_url: "https://..."
  check_days_ahead: 7
  timezone: "America/New_York"
```

### Website Fetchers
```yaml
fetchers:
  ncaa:
    base_url: "https://stats.ncaa.org"
    timeout: 30
  tfrr:
    base_url: "https://www.tfrrs.org"
    timeout: 30
```

### Player Database
```yaml
database:
  type: "sqlite"
  path: "data/stats.db"
```

### Milestone Detector
```yaml
milestones:
  basketball:
    points: [1000, 1500, 2000]
    rebounds: [500, 750, 1000]
```

### Email Notifier
```yaml
email:
  smtp_server: "smtp.gmail.com"
  smtp_port: 587
  sender_email: "your-email@example.com"
  sender_password: "your-app-password"
  recipients:
    - "recipient@example.com"
```

## Error Handling Contract

All modules should:

1. **Log errors** using Python logging
2. **Return sensible defaults** on error (empty list, None, False)
3. **Not crash** - handle exceptions gracefully
4. **Provide error details** in return objects when applicable

Example:
```python
def fetch_player_stats(player_id: str, sport: str) -> FetchResult:
    try:
        # Fetch logic
        return FetchResult(success=True, data=data)
    except Exception as e:
        logger.error(f"Error fetching stats: {e}")
        return FetchResult(success=False, error=str(e))
```

## Testing Interfaces

When writing tests, use mocks to simulate other modules:

```python
from unittest.mock import Mock
import pytest

def test_milestone_detector():
    # Mock the database
    mock_db = Mock()
    mock_db.get_player_stats.return_value = PlayerStats(...)

    detector = MilestoneDetector(mock_db, config)
    result = detector.check_player_milestones("p001")

    assert len(result) > 0
```

## Adding New Interfaces

If you need to add a new interface:

1. Document it in this file
2. Define clear input/output types
3. Add example usage
4. Update the data flow diagram
5. Notify team members of the change
