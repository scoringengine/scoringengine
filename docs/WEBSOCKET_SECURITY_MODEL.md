# WebSocket Security Model

This document explains the security architecture for WebSocket implementation in the scoring engine, specifically how team data isolation is maintained.

## Security Principle

**WebSocket events are broadcast signals, NOT data carriers.**

The WebSocket connection broadcasts a generic "something changed" signal to all connected clients. Clients then fetch their authorized data via authenticated API calls.

## Why This Approach?

### ❌ What We Don't Do (Insecure)

```javascript
// WRONG: Sending team-specific data via WebSocket
socket.emit('team_update', {
    team_id: 123,
    services: [...],  // ← DANGER: All clients receive this!
    score: 5000
});
```

**Problem**: All WebSocket clients receive all messages. If we send team data via WebSocket, Team A could see Team B's service status.

### ✅ What We Do (Secure)

```javascript
// RIGHT: Signal only, no sensitive data
socket.emit('scoreboard_update', {
    round: 42,
    timestamp: '2025-12-30T20:00:00Z'
});

// Client side: Each team fetches their OWN data
socket.on('scoreboard_update', function(data) {
    // Makes authenticated API call with session cookie
    $.ajax('/api/team/MY_TEAM_ID/services');  // ← API verifies session
});
```

**Benefits**:
- WebSocket carries no sensitive data
- Each team only sees their own data (via API authorization)
- Existing Flask-Login authentication still works
- No new authorization logic needed

## Page-by-Page Security Model

### Public Pages (No Authentication Needed)

#### scoreboard.html
- **Data**: Public scoreboard (all teams' scores)
- **Security**: None needed, data is public
- **WebSocket Event**: `scoreboard_update`
- **API Calls**:
  - `/api/scoreboard/get_bar_data` (public)
  - `/api/scoreboard/get_line_data` (public)

#### overview.html
- **Data**: Public service status (all teams)
- **Security**: None needed, data is public
- **WebSocket Event**: `scoreboard_update`
- **API Calls**:
  - `/api/overview/get_data` (public)
  - `/api/overview/get_round_data` (public)

### Authenticated Team Pages (Authorization Required)

#### services.html
- **Data**: Team-specific services and scores
- **Security**: API verifies `current_user.team.id` matches URL `{team_id}`
- **WebSocket Event**: `scoreboard_update` (public signal)
- **API Calls** (authenticated):
  - `/api/team/{team_id}/stats` → Checks user's team
  - `/api/team/{team_id}/services` → Checks user's team

**Security Flow**:
1. User logs in as Team Blue
2. WebSocket broadcasts: `{round: 42}` to everyone
3. Team Blue client calls: `/api/team/1/stats`
4. API layer checks: Is `current_user.team.id == 1`? ✓ Yes → Return data
5. Team Red client calls: `/api/team/2/stats`
6. API layer checks: Is `current_user.team.id == 2`? ✓ Yes → Return data

**No Data Leakage**: Each team only gets their own data because the API enforces team membership.

#### service.html
- **Data**: Service check history for one service
- **Security**: API verifies service belongs to user's team
- **WebSocket Event**: `scoreboard_update` (public signal)
- **API Calls** (authenticated):
  - `/api/service/{service_id}/checks` → Verifies service.team == current_user.team
  - `/api/team/{team_id}/services/status` → Checks user's team

**Security Flow**:
1. User views service #42 (belongs to Team Blue)
2. WebSocket broadcasts: `{round: 42}` to everyone
3. Team Blue client calls: `/api/service/42/checks`
4. API checks: Does service #42 belong to Team Blue? ✓ Yes → Return data
5. If Team Red tries: `/api/service/42/checks`
6. API checks: Does service #42 belong to Team Red? ✗ No → 403 Forbidden

**No Data Leakage**: Teams can only view services they own.

## Authorization Architecture

```
┌─────────────────────────────────────────────────────┐
│ WebSocket Layer (No Authorization)                  │
│                                                      │
│  ┌────────┐      scoreboard_update event           │
│  │ Engine │ ────────────────────────────────────►   │
│  └────────┘      {round: N, timestamp: T}           │
│                                                      │
│      Broadcasted to ALL clients in 'scoreboard' room│
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│ Client-Side (Browser)                               │
│                                                      │
│  socket.on('scoreboard_update', function(data) {    │
│    // Make authenticated API call for MY team       │
│    $.ajax('/api/team/MY_TEAM/services');            │
│  });                                                 │
│                                                      │
│  Cookie: session=abc123 (Flask-Login session)       │
└─────────────────────────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────┐
│ API Layer (Authorization Enforced)                  │
│                                                      │
│  @login_required                                     │
│  def get_team_services(team_id):                    │
│    if current_user.team.id != team_id:              │
│      return 403  # Forbidden                        │
│    return get_services(team_id)                     │
│                                                      │
│  ✓ Flask-Login verifies session                     │
│  ✓ Checks team ownership                            │
│  ✓ Returns only authorized data                     │
└─────────────────────────────────────────────────────┘
```

## Security Testing

### Test 1: Cross-Team Data Access

**Setup**:
1. Log in as Team Blue (ID=1)
2. Open browser DevTools → Console

**Test**:
```javascript
// Try to fetch Team Red's data (ID=2)
$.ajax('/api/team/2/services').then(
    data => console.log('SUCCESS (BAD!):', data),
    error => console.log('BLOCKED (GOOD!):', error.status)
);
```

**Expected Result**: `BLOCKED (GOOD!): 403` or redirect to login

**Why**: API layer checks `current_user.team.id != 2`

### Test 2: WebSocket Event Sniffing

**Setup**:
1. Log in as Team Blue
2. Open browser DevTools → Network → WS tab
3. Click on the WebSocket connection
4. Go to Messages tab

**Test**: Watch messages when round completes

**Expected Result**:
```json
{
  "type": "scoreboard_update",
  "data": {
    "round": 42,
    "timestamp": "2025-12-30T20:00:00Z"
  }
}
```

**Why**: No team-specific data in WebSocket events!

### Test 3: Service URL Manipulation

**Setup**:
1. Log in as Team Blue
2. Navigate to one of your services: `/service/123`
3. Note a service ID from another team (e.g., 456)

**Test**:
```
Navigate to: /service/456
```

**Expected Result**:
- Either: 403 Forbidden
- Or: Redirect to login
- Or: Error message "Unauthorized"

**Why**: Service #456 doesn't belong to Team Blue

### Test 4: Multiple Teams See Different Data

**Setup**:
1. Open two browsers (or incognito windows)
2. Browser A: Log in as Team Blue
3. Browser B: Log in as Team Red
4. Both navigate to `/services`

**Test**: Wait for round to complete

**Expected Result**:
- Both browsers see "scoreboard_update" in console
- Browser A shows Team Blue's services only
- Browser B shows Team Red's services only
- Different data despite same WebSocket event

**Why**: Each browser makes authenticated API call for their own team

## Common Security Questions

### Q: Can WebSocket connections be hijacked?

**A**: Yes, like any HTTP connection. That's why we:
1. Use HTTPS in production (wss:// protocol)
2. Don't send sensitive data via WebSocket
3. Rely on Flask session cookies for authentication
4. Keep authorization in the API layer

### Q: What if someone connects to WebSocket without logging in?

**A**: They receive the `scoreboard_update` event (which is public info: just round number). When they try to call the API, they'll be rejected or redirected to login.

### Q: Can Team A subscribe to a "Team B room"?

**A**: There are no team-specific rooms! Everyone joins the same `scoreboard` room and receives the same generic event. Teams are differentiated by API authorization, not WebSocket rooms.

### Q: Why not use team-specific WebSocket rooms?

**A**: We could, but it's more complex:
- Need to track which team each WebSocket belongs to
- Need to verify team membership on socket.emit
- Duplicate authorization logic (both WebSocket and API)
- Our approach is simpler: WebSocket = broadcast, API = authorization

### Q: What prevents a team from calling another team's API?

**A**: Flask-Login + explicit team checks in API endpoints:

```python
@mod.route('/api/team/<int:team_id>/services')
@login_required
def get_team_services(team_id):
    # Flask-Login provides current_user
    if current_user.team.id != team_id:
        abort(403)  # Forbidden
    # ... return data
```

## Best Practices

### ✅ DO

1. **Send minimal data via WebSocket**: Just event type, round number, timestamp
2. **Use API for data fetching**: Let Flask handle authentication
3. **Verify team ownership**: Check `current_user.team.id` in API endpoints
4. **Use existing auth**: Don't reinvent authentication for WebSocket
5. **Document security model**: Explain why it's safe

### ❌ DON'T

1. **Send team data via WebSocket**: Everyone receives WebSocket messages!
2. **Trust client-side team ID**: Always verify on server
3. **Skip authorization checks**: Just because WebSocket is "real-time" doesn't mean skip auth
4. **Create complex room structures**: Simple broadcast is easier to secure
5. **Expose service IDs**: Use API authorization to prevent enumeration

## Audit Checklist

Before deploying WebSocket updates:

- [ ] All WebSocket events contain only public data (round #, timestamp)
- [ ] All API endpoints have `@login_required` decorator
- [ ] Team-specific APIs verify `current_user.team.id`
- [ ] Service-specific APIs verify service ownership
- [ ] Tested cross-team data access (should fail)
- [ ] Tested WebSocket event content (no secrets)
- [ ] HTTPS enabled in production (wss:// instead of ws://)
- [ ] Session cookies are httpOnly and secure
- [ ] CORS properly configured (if needed)
- [ ] Documented security model

## Summary

**The WebSocket layer is a notification system, not a data transport.**

By keeping sensitive data out of WebSocket events and relying on authenticated API calls, we maintain strict team data isolation while providing real-time updates.

This architecture:
- ✅ Is simple to understand and audit
- ✅ Reuses existing authentication infrastructure
- ✅ Provides defense in depth (WebSocket + API layers)
- ✅ Prevents accidental data leakage
- ✅ Scales well (one event triggers many API calls)

The same session that authenticates your web page also authenticates your API calls, ensuring each team only sees their own data.
