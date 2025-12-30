# Load Testing with Locust

This directory contains Locust load tests for the Scoring Engine WebSocket implementation.

## Installation

```bash
pip install locust python-socketio
```

## Quick Start

### 1. Start Your Services

```bash
# Start all services
docker-compose up -d

# Or start individually:
bin/web      # Terminal 1
bin/worker   # Terminal 2
bin/engine   # Terminal 3
```

### 2. Run Basic Load Test

```bash
# From project root
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

Then open: http://localhost:8089

### 3. Configure Test Parameters

In the Web UI:
- **Number of users**: How many concurrent viewers to simulate
- **Spawn rate**: How many users to add per second
- **Host**: Your scoring engine URL

Example settings:
- **Small test**: 10 users, spawn rate 2
- **Medium test**: 50 users, spawn rate 5
- **Large test**: 200 users, spawn rate 10

## Test Scenarios

### Scenario 1: WebSocket Viewers (Recommended)

Tests the new WebSocket implementation:

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --only-summary
```

**User Classes**: `ScoreboardViewer`, `OverviewViewer`
- Connects via WebSocket
- Minimal polling (only initial load)
- Receives real-time updates

### Scenario 2: Polling Only (Baseline Comparison)

Tests the OLD polling-based approach:

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 5m \
    --user-classes PollingOnlyViewer
```

**User Class**: `PollingOnlyViewer`
- NO WebSocket
- Polls every 30 seconds
- Simulates old behavior

### Scenario 3: API Only

Tests just the API endpoints without WebSocket overhead:

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 50 \
    --spawn-rate 5 \
    --user-classes APIOnlyTester
```

### Scenario 4: Mixed Load

Simulate realistic mix of viewers:

```bash
# Edit locustfile.py and set user weights
# Run without --user-classes to use all types
locust -f tests/load/locustfile.py --host=http://localhost:8000
```

## Interpreting Results

### Key Metrics to Watch

1. **Response Time**
   - WebSocket connections: Should be <100ms
   - API endpoints: Should be <200ms (with caching)
   - Charts: Green = good, Yellow = acceptable, Red = slow

2. **Requests/Second (RPS)**
   - WebSocket mode: LOW RPS (only initial loads)
   - Polling mode: HIGH RPS (constant 30s polling)
   - Lower is better with WebSocket!

3. **Failure Rate**
   - Should be 0% for successful test
   - WebSocket failures indicate connection issues
   - API failures indicate server overload

4. **WebSocket Stats**
   - `connect`: Connection establishment time
   - `join_room`: Room subscription time
   - `scoreboard_update`: Update reception time

### Expected Performance

#### WebSocket Implementation (NEW)

**100 concurrent viewers:**
- Initial spike: ~200 requests (page loads)
- Steady state: ~5-10 req/min (only fallback polling)
- WebSocket connections: 100 persistent
- **Total API load**: MINIMAL

**Round completion:**
- 1 broadcast to all connected clients
- 0 additional API requests
- Updates arrive instantly

#### Polling Implementation (OLD)

**100 concurrent viewers:**
- Constant load: ~400 req/min
- Each viewer polls every 30s
- No persistent connections
- **Total API load**: HIGH

**Round completion:**
- No immediate notification
- Users see update in 0-30 seconds (random)
- Same polling load continues

### Performance Comparison

| Metric | WebSocket | Polling | Improvement |
|--------|-----------|---------|-------------|
| API Requests (100 users) | ~10/min | ~400/min | **97% reduction** |
| Update Latency | <100ms | 0-30s | **Instant** |
| Server Load | Minimal | High | **Significant** |
| Cache Hits | High | Medium | **Better** |
| Concurrent Connections | 100 WS | 0 | New overhead |

## Advanced Testing

### Test During Active Competition

Start a round-based test:

```bash
# Terminal 1: Run engine
bin/engine

# Terminal 2: Run load test
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 10m
```

Watch for:
- WebSocket broadcasts when rounds complete
- All clients update simultaneously
- No polling spam

### Stress Test

Find breaking point:

```bash
# Gradually increase load
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 500 \
    --spawn-rate 20 \
    --run-time 10m
```

Monitor:
- Server CPU/memory usage
- WebSocket connection limits
- Database connection pool
- Redis connections

### Headless Mode (CI/CD)

Run without Web UI:

```bash
locust -f tests/load/locustfile.py \
    --host=http://localhost:8000 \
    --users 100 \
    --spawn-rate 10 \
    --run-time 3m \
    --headless \
    --html report.html
```

### Custom Scenarios

Edit `locustfile.py` to:
- Adjust task weights (change `@task(N)` numbers)
- Add new user behaviors
- Simulate specific attack patterns
- Test edge cases

## Troubleshooting

### WebSocket Connection Failures

**Symptom**: High failure rate for WebSocket requests

**Causes**:
- nginx not proxying `/socket.io/` correctly
- Server not running with socketio.run()
- CORS issues
- Port 8000 not accessible

**Fix**:
```bash
# Check nginx config
cat configs/nginx.conf | grep socket.io

# Verify bin/web uses socketio.run()
grep socketio bin/web

# Test direct connection (bypass nginx)
locust --host=http://localhost:8000
```

### High Response Times

**Symptom**: Response times >1000ms

**Causes**:
- Database query performance
- Cache not working
- Too many concurrent users
- Server resource exhaustion

**Fix**:
```bash
# Check cache hit rate
redis-cli INFO stats | grep hits

# Monitor server resources
top
htop

# Check slow queries
# MySQL: Enable slow query log
# Check engine logs for round duration
```

### Rate Limiting / 429 Errors

If you see 429 errors, you may be hitting rate limits.

**Reduce load**:
```bash
locust --users 20 --spawn-rate 2
```

## Best Practices

1. **Start Small**: Begin with 10-20 users
2. **Ramp Gradually**: Use spawn-rate to avoid spike
3. **Monitor Servers**: Watch CPU, memory, connections
4. **Test Incrementally**: Increase load in stages
5. **Use Realistic Scenarios**: Match actual competition patterns
6. **Compare Baselines**: Test both WebSocket and Polling modes
7. **Test Edge Cases**: Network failures, reconnections
8. **Document Results**: Save reports for comparison

## Example Test Plan

### Pre-Competition Load Test

```bash
# Day before competition
# Test with 2x expected viewers

# 1. Baseline (current code)
git checkout main
locust --host=http://localhost:8000 --users 200 --spawn-rate 10 --run-time 5m --html baseline.html --headless

# 2. WebSocket (new code)
git checkout claude/scoring-engine-feature-iwxMh
locust --host=http://localhost:8000 --users 200 --spawn-rate 10 --run-time 5m --html websocket.html --headless

# 3. Compare reports
# baseline.html vs websocket.html
```

### During Competition Monitoring

```bash
# Light continuous load
locust --host=https://your-competition.com \
    --users 50 \
    --spawn-rate 5 \
    --run-time 4h \
    --html competition_load.html \
    --headless
```

## Results Analysis

After test completion:

1. **Download HTML report** from Locust UI
2. **Check statistics** table for:
   - Request counts
   - Response times (median, p95, p99)
   - Failure rates
3. **View charts**:
   - Response time over time
   - Users over time
   - RPS over time
4. **Compare** WebSocket vs Polling results

## Need More Help?

- Locust docs: https://docs.locust.io/
- Socket.IO Python: https://python-socketio.readthedocs.io/
- See `WEBSOCKET_TESTING.md` for manual testing
