# WebSocket Testing Guide

This guide covers testing the real-time WebSocket functionality for scoreboard and overview pages.

## Manual Functional Testing

### 1. Start the Services

Start all required services in separate terminals:

```bash
# Terminal 1: Start Redis
docker-compose up redis

# Terminal 2: Start MySQL
docker-compose up mysql

# Terminal 3: Start Web Server (with WebSocket support)
bin/web

# Terminal 4: Start Worker
bin/worker

# Terminal 5: Start Engine
bin/engine
```

### 2. Open Browser Developer Tools

1. Open your browser to `http://localhost:8000/scoreboard`
2. Open Developer Tools (F12)
3. Go to the **Console** tab
4. You should see:
   ```
   WebSocket connected
   Joined room: scoreboard
   ```

### 3. Monitor WebSocket Events

Watch the console for these events when a round completes:

```javascript
// Expected console output:
Scoreboard update received for round: 2
```

The charts should update **immediately** without page refresh.

### 4. Test Overview Page

1. Navigate to `http://localhost:8000/overview`
2. Watch console for same connection messages
3. When round completes, table and header should update instantly

### 5. Test Fallback Polling

To test the 1-minute fallback:

1. Stop the web server (`bin/web`)
2. Observe console shows: `WebSocket disconnected`
3. Wait 60 seconds
4. Restart web server
5. Should reconnect automatically

### 6. Network Tab Verification

In Developer Tools **Network** tab:

1. Filter by "WS" (WebSocket)
2. You should see a connection to `/socket.io/`
3. Click on it to see messages:
   - `2probe` (ping)
   - `3probe` (pong)
   - Scoreboard update events

### 7. Verify No Polling (When WebSocket Works)

With WebSocket connected:

1. Watch **Network** tab
2. Filter for `/api/scoreboard/get_bar_data`
3. Should see:
   - Initial load on page load
   - **NO requests** for 60+ seconds (no polling)
   - Only updates via WebSocket events

### 8. Test Multiple Browsers

Open scoreboard in multiple browser tabs/windows:

1. All should connect via WebSocket
2. All should update simultaneously when round completes
3. Check server logs for multiple connections

## Expected Server Logs

When WebSocket is working, you should see in `bin/web` output:

```
INFO - Starting Web v.X.X.X with WebSocket support
INFO - Client connected
INFO - Client joined scoreboard room
```

When engine completes a round:

```
INFO - Updating Caches
INFO - Broadcasting scoreboard update via WebSocket
```

## Troubleshooting

### WebSocket Not Connecting

Check browser console for errors:
- `connect_error`: Server not running or nginx misconfigured
- `polling error`: CORS or proxy issues

### Updates Not Happening

1. Verify engine is running (`bin/engine`)
2. Check engine logs for "Broadcasting scoreboard update"
3. Verify WebSocket connection in browser console
4. Check nginx is proxying `/socket.io/` correctly

### Fallback Polling Not Working

1. Check browser console for AJAX errors
2. Verify API endpoints return data: `curl http://localhost:8000/api/scoreboard/get_bar_data`
3. Look for JavaScript errors preventing setInterval

## Performance Monitoring

### Before WebSocket (30s polling):
- 2 API requests per 30 seconds = 4 req/min per client
- 10 viewers = 40 req/min
- 100 viewers = 400 req/min

### After WebSocket (1min fallback):
- 0 polling requests while connected
- Only during WebSocket failure: 2 req/min per client
- 100 viewers with WebSocket = ~0 req/min + instant updates

### Check Cache Hit Rate

```python
# In Python shell with Redis running:
from scoring_engine.cache import cache
cache.get('scoreboard_get_bar_data')  # Should be cached
```

## Success Criteria

✅ WebSocket connects on page load
✅ Console shows "joined scoreboard room"
✅ Updates appear instantly when round completes
✅ No polling requests in Network tab (when WS connected)
✅ Fallback polling works if WebSocket disconnected
✅ Multiple browsers all update simultaneously
✅ Server logs show broadcast events
✅ Charts update without page refresh
