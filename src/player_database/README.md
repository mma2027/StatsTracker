# Player Database Module

## Purpose
Manages storage and retrieval of player statistics data.

## Database Schema

### Players Table
```sql
CREATE TABLE players (
    player_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    sport TEXT NOT NULL,
    team TEXT DEFAULT 'Haverford',
    position TEXT,
    year TEXT,
    active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### Stats Table
```sql
CREATE TABLE stats (
    stat_id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id TEXT NOT NULL,
    stat_name TEXT NOT NULL,
    stat_value TEXT NOT NULL,
    season TEXT NOT NULL,
    date_recorded TIMESTAMP,
    game_id TEXT,
    notes TEXT,
    FOREIGN KEY (player_id) REFERENCES players(player_id)
)
```

## Interface

### PlayerDatabase Class

#### Player Operations
```python
def add_player(self, player: Player) -> bool
def get_player(self, player_id: str) -> Optional[Player]
def update_player(self, player: Player) -> bool
def get_all_players(self, sport: Optional[str] = None, active_only: bool = True) -> List[Player]
def search_players(self, name: str, sport: Optional[str] = None) -> List[Player]
```

#### Stats Operations
```python
def add_stat(self, stat_entry: StatEntry) -> bool
def get_player_stats(self, player_id: str, season: Optional[str] = None) -> Optional[PlayerStats]
```

## Models

### Player
- `player_id`: Unique identifier
- `name`: Player name
- `sport`: Sport name
- `team`: Team name (default: Haverford)
- `position`: Player position
- `year`: Academic year
- `active`: Whether player is currently active

### StatEntry
- `stat_id`: Auto-generated ID
- `player_id`: Reference to player
- `stat_name`: Name of statistic (e.g., "points", "rebounds")
- `stat_value`: Value of statistic
- `season`: Season identifier (e.g., "2023-24")
- `date_recorded`: When stat was recorded
- `game_id`: Optional link to specific game
- `notes`: Optional notes

### PlayerStats
- `player`: Player object
- `career_stats`: Dictionary of career statistics
- `season_stats`: Dictionary of season-by-season statistics
- `recent_entries`: List of recent stat entries

## Implementation Tasks

- [x] Create database schema
- [x] Implement player CRUD operations
- [x] Implement stat storage and retrieval
- [ ] Add data validation
- [ ] Implement backup/export functionality
- [ ] Add migration support for schema changes
- [ ] Optimize queries for large datasets
- [ ] Add bulk insert operations
- [ ] Implement PostgreSQL support (optional)
- [ ] Add transaction support

## Usage Examples

### Adding a Player
```python
from src.player_database import PlayerDatabase, Player

db = PlayerDatabase("data/stats.db")

player = Player(
    player_id="p001",
    name="John Doe",
    sport="basketball",
    position="Guard",
    year="Junior"
)

db.add_player(player)
```

### Adding Statistics
```python
from src.player_database import StatEntry
from datetime import datetime

stat = StatEntry(
    player_id="p001",
    stat_name="points",
    stat_value=25,
    season="2023-24",
    date_recorded=datetime.now()
)

db.add_stat(stat)
```

### Retrieving Player Stats
```python
stats = db.get_player_stats("p001", season="2023-24")
if stats:
    print(f"Points: {stats.get_stat('points', '2023-24')}")
    print(f"Career points: {stats.career_stats.get('points', 0)}")
```

### Searching Players
```python
players = db.search_players("John", sport="basketball")
for player in players:
    print(f"{player.name} - {player.sport}")
```

## Testing

Create tests in `tests/player_database/`:
- Test database initialization
- Test CRUD operations
- Test stat aggregation
- Test search functionality
- Test error handling

## Migration from SQLite to PostgreSQL

The code is designed to be extensible. To support PostgreSQL:

1. Create a new `PostgresDatabase` class inheriting from a base class
2. Implement the same interface methods
3. Use SQLAlchemy for database abstraction (recommended)
4. Update configuration to allow database type selection

## Integration Points

- **Used by**: Website fetcher (to store fetched data), Milestone detector (to analyze stats)
- **Uses**: Configuration for database path
- **Output**: Player and PlayerStats objects for other modules
