# Milestone Configuration Guide

This guide explains how to configure milestone alerts for different sports in StatsTracker.

## Overview

Milestones are career achievement thresholds that trigger notifications when players get close to reaching them. For example, alerting when a basketball player is within 10 points of reaching 1,000 career points.

## Configuration File

Milestones are configured in [config/config.yaml](../config/config.yaml) under the `milestones:` section.

## Basic Structure

```yaml
milestones:
  sport_name:
    STAT_NAME:
      - threshold_1
      - threshold_2
      - threshold_3
```

### Important Notes

1. **Sport Names**: Use the FULL database sport name (e.g., `mens_basketball`, not `basketball`)
2. **Stat Names**: Use the EXACT stat name from NCAA stats (case-sensitive!)
3. **Multiple Thresholds**: You can define multiple milestone levels for each stat

## Available Sport Names

- `mens_basketball`
- `womens_basketball`
- `mens_soccer`
- `womens_soccer`
- `field_hockey`
- `mens_lacrosse`
- `womens_lacrosse`
- `baseball`
- `softball`
- `womens_volleyball`
- `mens_track` (typically not used - track uses PR improvements)
- `womens_track` (typically not used)
- `mens_cross_country`
- `womens_cross_country`

## Finding Stat Names

To find the exact stat names for a sport:

1. **Update stats**:
   ```bash
   python main.py --update-stats
   ```

2. **Check CSV exports**:
   ```bash
   ls csv_exports/ncaa/
   cat csv_exports/ncaa/mens_basketball_*_seasonal_career.csv
   ```

3. **Common stat names**:
   - Basketball: `PTS`, `"Tot Reb"`, `AST`, `STL`, `BLK`
   - Soccer: `G`, `A`, `Pts`
   - Lacrosse: `G`, `A`
   - Baseball/Softball: `H`, `RBI`, `HR`, `AVG`
   - Volleyball: `Kills`, `Digs`, `Aces`, `Blocks`

## Example Configurations

### Basketball

```yaml
milestones:
  mens_basketball:
    PTS:  # Points
      - 1000
      - 1500
      - 2000
    "Tot Reb":  # Total Rebounds (quotes needed for spaces!)
      - 500
      - 750
      - 1000
    AST:  # Assists
      - 300
      - 500
      - 750
```

### Soccer

```yaml
milestones:
  mens_soccer:
    G:  # Goals
      - 20
      - 30
      - 40
    A:  # Assists
      - 15
      - 25
      - 35
```

### Baseball

```yaml
milestones:
  baseball:
    H:  # Hits
      - 100
      - 150
      - 200
    RBI:  # Runs Batted In
      - 75
      - 100
      - 150
    HR:  # Home Runs
      - 10
      - 20
      - 30
```

### Volleyball

```yaml
milestones:
  womens_volleyball:
    Kills:
      - 500
      - 750
      - 1000
    Digs:
      - 500
      - 750
      - 1000
    Aces:
      - 50
      - 75
      - 100
```

## Proximity Threshold

The proximity threshold determines how close a player must be to trigger an alert. This is configured separately in the `notifications` section:

```yaml
notifications:
  proximity_threshold: 10  # Alert when within 10 units of milestone
```

### Example

With `proximity_threshold: 10`:
- A player with 992 points → Alert for 1000-point milestone (8 points away)
- A player with 975 points → No alert (25 points away, outside threshold)

You can also override this when calling the detector programmatically:

```python
# Check with threshold of 50
detector.check_all_players_milestones(sport='mens_basketball', proximity_threshold=50)
```

## Common Pitfalls

### 1. Stat Name Mismatch

**Problem:**
```yaml
mens_basketball:
  points:  # ❌ Wrong! NCAA uses "PTS"
    - 1000
```

**Solution:**
```yaml
mens_basketball:
  PTS:  # ✅ Correct!
    - 1000
```

### 2. Missing Quotes for Stat Names with Spaces

**Problem:**
```yaml
mens_basketball:
  Tot Reb:  # ❌ YAML parsing error!
    - 500
```

**Solution:**
```yaml
mens_basketball:
  "Tot Reb":  # ✅ Quotes required!
    - 500
```

### 3. Using Generic Sport Names

**Problem:**
```yaml
basketball:  # ❌ Database has mens_basketball and womens_basketball
  PTS:
    - 1000
```

**Solution:**
```yaml
mens_basketball:  # ✅ Use full sport name
  PTS:
    - 1000
womens_basketball:  # Configure separately
  PTS:
    - 1000
```

## Testing Milestones

### Check What Milestones Are Loaded

```bash
python -c "
from src.milestone_detector import MilestoneDetector
from src.player_database import PlayerDatabase
import yaml

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

db = PlayerDatabase('data/stats.db')
detector = MilestoneDetector(db, config.get('milestones', {}))

print(f'Total milestones loaded: {len(detector.milestones)}')
for milestone in detector.milestones[:10]:
    print(f'  {milestone.sport}: {milestone.stat_name} -> {milestone.threshold}')
"
```

### Check for Players Close to Milestones

```bash
python -c "
from src.milestone_detector import MilestoneDetector
from src.player_database import PlayerDatabase
import yaml

with open('config/config.yaml') as f:
    config = yaml.safe_load(f)

db = PlayerDatabase('data/stats.db')
detector = MilestoneDetector(db, config.get('milestones', {}))

# Check men's basketball with threshold of 50
proximities = detector.check_all_players_milestones(
    sport='mens_basketball',
    proximity_threshold=50
)

print(f'Players close to milestones: {len([p for p, pl in proximities.items() if pl])}')
for player_id, prox_list in proximities.items():
    if prox_list:
        player = db.get_player(player_id)
        print(f'\n{player.name}:')
        for prox in prox_list:
            print(f'  {prox.milestone.stat_name}: {prox.current_value}/{prox.milestone.threshold} (needs {prox.distance} more)')
"
```

## Customizing for Your School

### Adjusting Thresholds

Different schools may want different milestone thresholds based on:
- Historical achievement levels
- School size (D1 vs D3)
- Program competitiveness

**Division III Example** (lower thresholds):
```yaml
mens_basketball:
  PTS:
    - 750   # Lower than 1000
    - 1250
    - 1750
```

**Division I Example** (higher thresholds):
```yaml
mens_basketball:
  PTS:
    - 1500
    - 2000
    - 2500
```

### Adding New Sports

To add milestones for a sport not yet configured:

1. **Check if stats exist**:
   ```bash
   python main.py --update-stats
   ls csv_exports/ncaa/ | grep "your_sport"
   ```

2. **Find stat names**:
   ```bash
   cat csv_exports/ncaa/your_sport_*_seasonal_career.csv | head -1
   ```

3. **Add to config**:
   ```yaml
   your_sport_name:
     STAT_NAME:
       - threshold_1
       - threshold_2
   ```

## Advanced: Sport-Specific Notes

### Track & Field

Track milestones are typically **PR improvements** rather than career totals. These require different logic:

```yaml
# Not currently implemented - placeholder
mens_track:
  pr_improvement: 0.05  # 5% improvement
```

### Time-Based Milestones

For sports with time-based achievements (e.g., track 5k times):

```yaml
# Not currently implemented - placeholder
mens_cross_country:
  5k_time: ["16:00", "15:30", "15:00"]  # Faster is better
```

## Troubleshooting

### No Milestones Detected

1. **Check sport name**:
   ```bash
   sqlite3 data/stats.db "SELECT DISTINCT sport FROM players;"
   ```

2. **Check stat names in database**:
   ```bash
   sqlite3 data/stats.db "SELECT DISTINCT stat_name FROM stats WHERE player_id IN (SELECT player_id FROM players WHERE sport='mens_basketball');"
   ```

3. **Verify config loading**:
   ```bash
   python -c "import yaml; print(yaml.safe_load(open('config/config.yaml'))['milestones'])"
   ```

### Incorrect Proximity Calculations

If milestone alerts seem wrong, check the player's actual stats:

```bash
python -c "
from src.player_database import PlayerDatabase

db = PlayerDatabase('data/stats.db')
# Find player
players = [p for p in db.get_all_players() if 'Player Name' in p.name]
if players:
    player = players[0]
    stats = db.get_player_stats(player.player_id)
    print(stats.career_stats)
"
```

## Related Documentation

- [Daily Automation Setup](DAILY_AUTOMATION_README.md)
- [Configuration Guide](getting_started.md)
- [Email Templates](../src/email_notifier/templates.py)
