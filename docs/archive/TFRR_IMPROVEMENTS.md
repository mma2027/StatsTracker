# TFRR Scraper Improvements - Anti-Rate-Limiting

## Overview
Implemented advanced anti-rate-limiting and anti-detection features for the TFRR scraper to avoid 403 errors and rate limiting when fetching athlete data.

## Date
January 13, 2026

## Problems Addressed
- **403 Forbidden errors** - TFRR was blocking requests due to bot detection
- **Rate limiting** - Too many requests in short time periods
- **No retry logic** - Requests failed permanently on first error
- **Fixed delays** - Predictable 3-second delays looked automated
- **Single user agent** - Easy to detect and block

## Improvements Implemented

### 1. Smart Delay System
**File**: [src/website_fetcher/tfrr_fetcher.py:83-112](src/website_fetcher/tfrr_fetcher.py#L83-L112)

- **Randomized base delays**: 3-7 seconds (instead of fixed 3 seconds)
- **Extended breaks**: Every 10-15 requests, takes 15-30 second break
- **Exponential backoff**: On consecutive errors, increases delay progressively
- **Jitter**: Adds random variation (0-30%) to backoff delays

```python
# Base delay: 3-7 seconds (randomized)
base_delay = random.uniform(3.0, 7.0)

# Exponential backoff on errors
if self.consecutive_errors > 0:
    backoff = min(2 ** self.consecutive_errors, 60)  # Max 60s
    jitter = random.uniform(0, backoff * 0.3)
    total_delay = base_delay + backoff + jitter
```

### 2. User Agent Rotation
**File**: [src/website_fetcher/tfrr_fetcher.py:28-37](src/website_fetcher/tfrr_fetcher.py#L28-L37)

- **Pool of 7 realistic user agents** (Chrome, Safari, Firefox on Mac/Windows)
- **Random selection** on each fetcher initialization
- **Rotation on retries** - Changes user agent if request fails

```python
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    # ... 5 more
]
```

### 3. Exponential Backoff Retry Logic
**File**: [src/website_fetcher/tfrr_fetcher.py:114-202](src/website_fetcher/tfrr_fetcher.py#L114-L202)

- **Max 3 retries** with exponential backoff
- **403 handling**: 8s → 16s → 32s wait (max 5 min)
- **429 handling**: 16s → 32s → 64s wait (max 15 min)
- **503 handling**: 30-60s random wait
- **Timeout handling**: 5-10s random wait before retry

```python
if response.status_code == 403:
    wait_time = min(2 ** (attempt + 3), 300)  # 8s, 16s, 32s... max 5 min
    jitter = random.uniform(0, wait_time * 0.2)
    total_wait = wait_time + jitter
    time.sleep(total_wait)
```

### 4. Selenium Anti-Detection
**File**: [src/website_fetcher/tfrr_fetcher.py:794-856](src/website_fetcher/tfrr_fetcher.py#L794-L856)

Enhanced Selenium driver with anti-bot detection measures:

- **New headless mode** (`--headless=new`)
- **Randomized window sizes** (1900-1920 x 1060-1080)
- **Random user agents** from pool
- **Disabled automation features**:
  - `--disable-blink-features=AutomationControlled`
  - `excludeSwitches: ["enable-automation"]`
  - `useAutomationExtension: False`
- **CDP commands to mask webdriver**:
  ```javascript
  Object.defineProperty(navigator, 'webdriver', {
      get: () => undefined  // Hide webdriver property
  });
  ```
- **Randomized timeouts** (15-20 seconds)

### 5. Persistent Session Management
**File**: [src/website_fetcher/tfrr_fetcher.py:57-63](src/website_fetcher/tfrr_fetcher.py#L57-L63)

- **Session object** maintains cookies across requests
- **Request tracking** monitors consecutive errors
- **State management** tracks last request time for smart delays

```python
self.session = requests.Session()  # Persistent session
self.request_count = 0  # Track requests
self.consecutive_errors = 0  # Track errors for backoff
```

### 6. Enhanced HTTP Headers
**File**: [src/website_fetcher/tfrr_fetcher.py:66-77](src/website_fetcher/tfrr_fetcher.py#L66-L77)

More realistic browser headers:
- `DNT: 1` (Do Not Track)
- `Sec-Fetch-Dest: document`
- `Sec-Fetch-Mode: navigate`
- `Sec-Fetch-Site: none`
- `Accept-Language: en-US,en;q=0.9`

## Updated Methods

All fetch methods now use the smart retry logic:

### `fetch_player_stats()`
**File**: [src/website_fetcher/tfrr_fetcher.py:204-249](src/website_fetcher/tfrr_fetcher.py#L204-L249)
- Uses `_make_request_with_retry()` instead of plain `requests.get()`
- Falls back to Selenium with anti-detection if needed

### `fetch_team_stats()`
**File**: [src/website_fetcher/tfrr_fetcher.py:251-309](src/website_fetcher/tfrr_fetcher.py#L251-L309)
- Applies `_smart_delay()` before Selenium requests
- Tracks request count for Selenium calls too
- Randomized wait times (4-6 seconds instead of fixed 5)

### `search_player()`
**File**: [src/website_fetcher/tfrr_fetcher.py:456-494](src/website_fetcher/tfrr_fetcher.py#L456-L494)
- Uses smart retry logic for search requests

### `fetch_event_results()`
**File**: [src/website_fetcher/tfrr_fetcher.py:536-570](src/website_fetcher/tfrr_fetcher.py#L536-L570)
- Uses smart retry for event-specific fetches

## CSV Export Script Update
**File**: [scripts/fetch_tfrr_to_csv.py:123-124](scripts/fetch_tfrr_to_csv.py#L123-L124)

Removed old manual rate limiting logic:
- ❌ Removed fixed 3-second `time.sleep(3)`
- ❌ Removed manual 15-minute wait on failures
- ✅ Now relies on built-in fetcher rate limiting

## Testing
**File**: [test_tfrr_improved.py](test_tfrr_improved.py)

Created test script to verify improvements:
```bash
python test_tfrr_improved.py
```

**Test Results** (Jan 13, 2026):
```
✓ Successfully fetched roster: 48 athletes
✓ Fetched PRs for 3 test athletes
✓ No 403 errors encountered
✓ All anti-detection measures working
```

## How to Use

The improvements are automatic - no changes needed to existing code:

```python
from src.website_fetcher.tfrr_fetcher import TFRRFetcher

fetcher = TFRRFetcher()

# Automatically uses smart delays, retries, and anti-detection
result = fetcher.fetch_player_stats(athlete_id, "track")
```

## Benefits

1. **Reduced 403 errors** - Anti-detection measures make requests look more human
2. **Automatic recovery** - Exponential backoff handles temporary rate limits
3. **Better success rate** - Multiple retries with increasing delays
4. **Unpredictable timing** - Randomization prevents pattern detection
5. **Maintained performance** - Extended breaks prevent long-term blocking

## Performance Characteristics

- **Average delay per request**: 3-7 seconds
- **Extended break frequency**: Every 10-15 requests (15-30 seconds)
- **Max retry delay**: 5 minutes (for 403), 15 minutes (for 429)
- **Expected time for 50 athletes**: ~10-15 minutes (vs ~2.5 minutes previously)

## Monitoring

The fetcher tracks:
- `request_count` - Total requests made
- `consecutive_errors` - Current error streak (for backoff)
- `last_request_time` - For delay calculations

Access via:
```python
print(f"Requests: {fetcher.request_count}")
print(f"Errors: {fetcher.consecutive_errors}")
```

## Future Enhancements (Optional)

If issues persist, consider:
1. **Proxy rotation** - Use multiple IP addresses
2. **Browser fingerprinting** - More advanced Canvas/WebGL spoofing
3. **Cookie management** - Clear cookies periodically
4. **Request prioritization** - Fetch critical athletes first
5. **Caching layer** - Store results to reduce requests

## Files Modified

1. [src/website_fetcher/tfrr_fetcher.py](src/website_fetcher/tfrr_fetcher.py) - Core improvements
2. [scripts/fetch_tfrr_to_csv.py](scripts/fetch_tfrr_to_csv.py) - Removed old rate limiting
3. [test_tfrr_improved.py](test_tfrr_improved.py) - New test script

## Compatibility

✅ **Backward compatible** - No breaking changes to public API
✅ **Drop-in replacement** - Existing code works without modification
✅ **Same return types** - All methods return `FetchResult` as before
