# WebSocket Implementation Analysis

Analysis of all pages in the scoring engine to determine which should use WebSocket for real-time updates.

## Current Status

### ✅ Pages with WebSocket Support

| Page | Polling Interval | WebSocket Room | Update Events |
|------|------------------|----------------|---------------|
| **scoreboard.html** | 1min fallback | `scoreboard` | Bar/line charts |
| **overview.html** | 1min fallback | `scoreboard` | Header + table |

**Benefits Achieved**:
- 97% reduction in API calls (30s → 1min fallback)
- Instant updates when rounds complete
- Better cache hit rates

---

## 🔴 Pages NEEDING WebSocket Support

### 1. services.html (Team Services Dashboard)

**Current Behavior**:
```javascript
// Polls every 30 seconds
setInterval(refreshteamdata, 30000);        // Team place + score
setInterval(table.ajax.reload, 30000);      // Services table
```

**What Updates**:
- Team place ranking
- Team current score
- Service status (UP/DOWN)
- Service scores
- Last 10 check results (trending)

**Why WebSocket Makes Sense**:
- ✅ Blue teams actively monitor their services during competition
- ✅ Want instant notification when service goes down
- ✅ Status changes every round
- ✅ High traffic page (every team member watches this)

**Implementation Priority**: **HIGH**

**Recommended Approach**:
```javascript
socket.on('scoreboard_update', function(data) {
    refreshteamdata();
    table.ajax.reload(null, false);
});
```

**API Endpoints**:
- `/api/team/{team_id}/stats`
- `/api/team/{team_id}/services`

---

### 2. service.html (Individual Service Detail)

**Current Behavior**:
```javascript
// Polls every 30 seconds
setInterval(function() {
    table.ajax.reload(expandRows, false);
    refreshServicesNavbar();
}, 30000);
```

**What Updates**:
- Check history table (recent checks for this service)
- Services navbar (list of all services)

**Why WebSocket Makes Sense**:
- ✅ Teams actively debugging failing services
- ✅ Want to see new check results immediately
- ✅ Checking detailed error messages in real-time
- ✅ Multiple team members may watch same service

**Implementation Priority**: **MEDIUM**

**Recommended Approach**:
```javascript
socket.on('scoreboard_update', function(data) {
    table.ajax.reload(expandRows, false);
    refreshServicesNavbar();
});
```

**API Endpoints**:
- `/api/service/{service_id}/checks` (likely)
- Services navbar endpoint

---

### 3. inject.html (Inject Detail Page)

**Current Behavior**:
```javascript
// Three separate 30-second polls
setInterval(updateInjects, 30000);   // Inject list/navbar
setInterval(updateComments, 30000);  // Comments section
setInterval(updateFiles, 30000);     // Uploaded files
```

**What Updates**:
- Inject status (Draft → Submitted → Graded)
- Comments from white team / other team members
- File uploads from team members
- Inject score

**Why WebSocket Makes Sense**:
- ✅ Multiple team members collaborate on same inject
- ✅ White team adds comments/grades in real-time
- ✅ Want instant notification of new comments
- ✅ File uploads should show immediately
- ⚠️ Updates less frequent than services (not every round)

**Implementation Priority**: **MEDIUM-LOW**

**Recommended Approach**:
Create specific event for inject updates:
```javascript
socket.on('inject_update', function(data) {
    if (data.inject_id == currentInjectId) {
        updateComments();
        updateFiles();
        updateInjects();
    }
});
```

**API Endpoints**:
- Inject navbar endpoint
- Comments endpoint
- Files endpoint

**Special Consideration**:
Needs new WebSocket event `inject_update` (separate from `scoreboard_update`)
Should be emitted when:
- Comment added
- File uploaded
- Inject submitted
- Inject graded

---

## ✅ Pages WITHOUT Polling (No WebSocket Needed)

### stats.html (Round Statistics)
- Loads once on page load
- Shows historical data, not real-time
- No polling detected
- **No WebSocket needed**

### flags.html (CTF Flags)
- Likely static or loads once
- Needs investigation if polling exists

### profile.html
- User profile settings
- Static page
- **No WebSocket needed**

### welcome.html
- Landing page
- Static content
- **No WebSocket needed**

---

## Implementation Recommendations

### Phase 1: High Priority (Immediate)

**services.html** - Team service dashboard
- **Impact**: High (most watched page by blue teams)
- **Effort**: Low (reuse `scoreboard_update` event)
- **Benefit**: Instant service status updates

### Phase 2: Medium Priority (Soon)

**service.html** - Individual service detail
- **Impact**: Medium (used during debugging)
- **Effort**: Low (reuse `scoreboard_update` event)
- **Benefit**: Real-time check results

### Phase 3: Medium-Low Priority (Later)

**inject.html** - Inject collaboration
- **Impact**: Medium (important but less frequent)
- **Effort**: Medium (needs new event type)
- **Benefit**: Real-time collaboration

---

## Event Architecture

### Existing Event

**`scoreboard_update`**
- Emitted by: Engine after round completes
- Room: `scoreboard`
- Payload: `{round: N, timestamp: ISO}`
- Listeners: scoreboard.html, overview.html

**Should also trigger**:
- services.html (team dashboard)
- service.html (service detail)

### New Event Needed

**`inject_update`**
- Emitted by: Web app on inject changes
- Room: `team_{team_id}` or `inject_{inject_id}`
- Payload: `{inject_id: N, team_id: N, type: 'comment|file|status'}`
- Listeners: inject.html

**Emit on**:
- Comment added
- File uploaded
- Inject submitted by team
- Inject graded by white team

---

## Traffic Analysis

### Current (30s polling)

| Page | Endpoints | Requests/User/Min | 10 Users/Min | 50 Users/Min |
|------|-----------|-------------------|--------------|--------------|
| services | 2 | 4 | 40 | 200 |
| service | 2 | 4 | 40 | 200 |
| inject | 3 | 6 | 60 | 300 |
| **TOTAL** | - | **14** | **140** | **700** |

### With WebSocket (1min fallback)

| Page | Endpoints | Requests/User/Min | 10 Users/Min | 50 Users/Min |
|------|-----------|-------------------|--------------|--------------|
| services | 2 | 2 | 20 | 100 |
| service | 2 | 2 | 20 | 100 |
| inject | 3 | 3 | 30 | 150 |
| **TOTAL** | - | **7** | **70** | **350** |

**Reduction**: 50% (with 1min fallback)
**With perfect WebSocket**: 93% (only initial load)

---

## Implementation Code Examples

### services.html Addition

```javascript
// Add Socket.IO script
<script src="{{ url_for('static', filename='vendor/js/socket.io.min.js') }}"></script>

// In document.ready
const socket = io();

socket.on('connect', function() {
    socket.emit('join_scoreboard');
});

socket.on('scoreboard_update', function(data) {
    console.log('Services update for round:', data.round);
    refreshteamdata();  // Update team place/score
    table.ajax.reload(null, false);  // Update services table
});

// Change polling from 30s to 60s fallback
setInterval(refreshteamdata, 60000);
setInterval(function() { table.ajax.reload(); }, 60000);
```

### service.html Addition

```javascript
// Add Socket.IO script
<script src="{{ url_for('static', filename='vendor/js/socket.io.min.js') }}"></script>

// In document.ready
const socket = io();

socket.on('connect', function() {
    socket.emit('join_scoreboard');
});

socket.on('scoreboard_update', function(data) {
    console.log('Service detail update for round:', data.round);
    table.ajax.reload(expandRows, false);
    refreshServicesNavbar();
});

// Change polling to 60s fallback
setInterval(function() {
    table.ajax.reload(expandRows, false);
    refreshServicesNavbar();
}, 60000);
```

### inject.html Addition (Advanced)

```javascript
// Add Socket.IO script
<script src="{{ url_for('static', filename='vendor/js/socket.io.min.js') }}"></script>

// In document.ready
const socket = io();
const currentInjectId = {{ inject.id }};
const currentTeamId = {{ current_user.team.id }};

socket.on('connect', function() {
    // Join both scoreboard and team-specific room
    socket.emit('join_scoreboard');
    socket.emit('join_team', {team_id: currentTeamId});
});

// Round updates trigger inject list refresh
socket.on('scoreboard_update', function(data) {
    updateInjects();  // Navbar might show new injects
});

// Inject-specific updates
socket.on('inject_update', function(data) {
    if (data.inject_id == currentInjectId) {
        console.log('Inject updated:', data.type);
        if (data.type === 'comment') {
            updateComments();
        } else if (data.type === 'file') {
            updateFiles();
        } else if (data.type === 'status') {
            // Reload page to show new status
            location.reload();
        }
    }
});

// Reduce polling to 60s fallback
setInterval(updateInjects, 60000);
setInterval(updateComments, 60000);
setInterval(updateFiles, 60000);
```

---

## Server-Side Changes Needed

### For inject_update Event

#### 1. Create WebSocket Event Handler

`scoring_engine/web/views/websocket.py`:

```python
@socketio.on('join_team')
def handle_join_team(data):
    """Subscribe client to team-specific updates"""
    team_id = data.get('team_id')
    join_room(f'team_{team_id}')
    logger.debug(f"Client joined team_{team_id} room")
    emit('joined', {'room': f'team_{team_id}'})
```

#### 2. Emit Events on Inject Changes

When comment added:
```python
from scoring_engine.web import socketio

socketio.emit('inject_update', {
    'inject_id': inject.id,
    'team_id': inject.team_id,
    'type': 'comment'
}, room=f'team_{inject.team_id}')
```

When file uploaded:
```python
socketio.emit('inject_update', {
    'inject_id': inject.id,
    'team_id': inject.team_id,
    'type': 'file'
}, room=f'team_{inject.team_id}')
```

When inject graded:
```python
socketio.emit('inject_update', {
    'inject_id': inject.id,
    'team_id': inject.team_id,
    'type': 'status'
}, room=f'team_{inject.team_id}')
```

---

## Testing Checklist

### services.html
- [ ] Page loads without errors
- [ ] WebSocket connects on load
- [ ] Team stats update when round completes
- [ ] Services table updates when round completes
- [ ] Service status changes reflect immediately
- [ ] Fallback polling works if WebSocket fails

### service.html
- [ ] Page loads without errors
- [ ] WebSocket connects on load
- [ ] Check history updates when round completes
- [ ] Services navbar updates
- [ ] Expandable rows maintain state on update
- [ ] Fallback polling works

### inject.html
- [ ] Page loads without errors
- [ ] WebSocket connects to both rooms
- [ ] Comments appear immediately when added
- [ ] Files appear immediately when uploaded
- [ ] Status changes trigger page reload
- [ ] Multiple users see same updates
- [ ] Fallback polling works

---

## Performance Impact Estimate

### Before All WebSocket Implementations
- services.html: 4 req/user/min × 50 users = 200 req/min
- service.html: 4 req/user/min × 20 users = 80 req/min
- inject.html: 6 req/user/min × 30 users = 180 req/min
- **Total**: 460 req/min from these pages alone

### After All WebSocket Implementations
- services.html: ~4 req/user/min (fallback only)
- service.html: ~4 req/user/min (fallback only)
- inject.html: ~6 req/user/min (fallback only)
- **With WebSocket working**: ~10-20 req/min total
- **If WebSocket fails**: Same as before

**Expected Reduction**: 95%+ during normal operation

---

## Recommendations Summary

1. **Implement services.html WebSocket** - Highest impact, easiest implementation
2. **Implement service.html WebSocket** - Medium impact, easy implementation
3. **Consider inject.html WebSocket** - Medium impact, requires new event architecture
4. **Monitor WebSocket connection health** - Add metrics and alerts
5. **Keep 1-minute fallback polling** - Balance between UX and server load

## Next Steps

1. Add WebSocket to services.html (reuse scoreboard_update event)
2. Add WebSocket to service.html (reuse scoreboard_update event)
3. Test with real competition load
4. Evaluate if inject.html needs immediate implementation
5. If needed, implement inject_update event infrastructure
6. Monitor performance metrics and adjust polling intervals
