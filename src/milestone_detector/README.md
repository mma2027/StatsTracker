# Milestone Detector Module

## Purpose
Analyzes player statistics to identify who is close to achieving milestones.

## Interface

### MilestoneDetector Class

#### Methods

```python
def check_player_milestones(
    self,
    player_id: str,
    proximity_threshold: int = 10
) -> List[MilestoneProximity]:
    """Check if a player is close to any milestones"""

def check_all_players_milestones(
    self,
    sport: Optional[str] = None,
    proximity_threshold: int = 10
) -> Dict[str, List[MilestoneProximity]]:
    """Check all players for milestone proximity"""

def get_priority_alerts(
    self,
    sport: Optional[str] = None
) -> List[MilestoneProximity]:
    """Get high-priority milestone alerts"""
```

## Models

### Milestone
Represents a milestone target:
- `milestone_id`: Unique identifier
- `sport`: Sport name
- `stat_name`: Statistic name
- `threshold`: Milestone value
- `milestone_type`: Type of milestone (career, season, PR, etc.)
- `description`: Human-readable description
- `priority`: Priority level (1=high, 2=medium, 3=low)

### MilestoneProximity
Represents how close a player is to a milestone:
- `player_id`: Player identifier
- `player_name`: Player name
- `milestone`: Associated Milestone object
- `current_value`: Current stat value
- `distance`: Distance from milestone
- `percentage`: Progress as percentage
- `estimated_games_to_milestone`: Estimated games needed

## Milestone Types

1. **CAREER_TOTAL**: Cumulative career statistics
   - Example: 1000 career points

2. **SEASON_TOTAL**: Single season statistics
   - Example: 500 points in current season

3. **PERSONAL_RECORD**: Personal bests
   - Example: Breaking 11 seconds in 100m

4. **GAME_PERFORMANCE**: Single game achievements
   - Example: 30+ points in a game

5. **AVERAGE**: Statistical averages
   - Example: 20 points per game average

## Configuration

Milestones are defined in `config/config.yaml`:

```yaml
milestones:
  basketball:
    points: [500, 1000, 1500, 2000]
    rebounds: [300, 500, 750, 1000]
    assists: [200, 300, 500]
  track:
    pr_improvement: 0.05  # 5% improvement
  soccer:
    goals: [10, 20, 30, 40]
    assists: [10, 15, 25]
```

## Implementation Tasks

- [x] Create basic milestone detection logic
- [ ] Implement all milestone types
- [ ] Add sport-specific milestone logic
- [ ] Improve games-to-milestone estimation
- [ ] Add historical milestone achievement tracking
- [ ] Implement trend analysis for predictions
- [ ] Add configurable notification thresholds
- [ ] Create milestone achievement history

## Usage Examples

### Check Single Player
```python
from src.milestone_detector import MilestoneDetector
from src.player_database import PlayerDatabase

db = PlayerDatabase("data/stats.db")
detector = MilestoneDetector(db, milestone_config)

proximities = detector.check_player_milestones("p001", proximity_threshold=10)
for prox in proximities:
    print(f"{prox.player_name} is {prox.distance} away from {prox.milestone.description}")
    print(f"Progress: {prox.percentage:.1f}%")
```

### Check All Players
```python
all_proximities = detector.check_all_players_milestones(sport="basketball")
for player_id, proximities in all_proximities.items():
    print(f"\nPlayer {player_id}:")
    for prox in proximities:
        print(f"  - {prox.milestone.description}: {prox.percentage:.1f}%")
```

### Get Priority Alerts
```python
priority_alerts = detector.get_priority_alerts(sport="basketball")
print(f"Found {len(priority_alerts)} high-priority alerts")
for alert in priority_alerts:
    print(f"{alert.player_name}: {alert.milestone.description}")
```

## Sport-Specific Logic

Different sports may need different milestone calculation logic:

### Basketball
- Cumulative stats (points, rebounds, assists)
- Per-game averages
- Shooting percentages

### Track & Field
- Personal records (time/distance improvements)
- Championship qualifying standards
- Season bests

### Soccer
- Goals and assists
- Clean sheets (for goalkeepers)
- Minutes played

## Testing

Create tests in `tests/milestone_detector/`:
- Test milestone proximity calculation
- Test different milestone types
- Test priority alert filtering
- Test edge cases (negative distances, etc.)
- Test with mock player data

## Integration Points

- **Used by**: Email notifier (to send alerts), Main orchestrator
- **Uses**: Player database (to get statistics)
- **Input**: Player statistics from database
- **Output**: MilestoneProximity objects indicating who to notify
