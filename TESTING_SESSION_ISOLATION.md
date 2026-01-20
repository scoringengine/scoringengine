# Testing Multi-User Session Isolation

This guide helps you verify that the Flask-SQLAlchemy migration properly isolates user sessions and prevents data contamination.

## What We're Testing For

The migration from a global `scoped_session` to Flask-SQLAlchemy's per-request sessions should prevent:

1. **Data Leakage** - User A shouldn't see User B's data
2. **Stale Data** - Refreshing should show current data, not cached stale data
3. **Session Contamination** - Concurrent requests shouldn't interfere with each other
4. **Race Conditions** - Multiple users accessing the same resources simultaneously

## Quick Start

### 1. Start the Application

```bash
# From the scoringengine directory
python bin/web
```

The app will start on `http://localhost:8000`

### 2. Ensure Test Users Exist

You need at least 2-3 test users from different teams. If you don't have them:

```bash
# Option A: Run the setup with a test competition
python bin/setup examples/example-competition.yaml

# Option B: Create users manually via Python console
python -c "
from scoring_engine.web import create_app
from scoring_engine.db import db
from scoring_engine.models.user import User
from scoring_engine.models.team import Team

app = create_app()
with app.app_context():
    # Create teams and users as needed
    team1 = db.session.query(Team).filter_by(name='Team 1').first()
    if team1:
        user = User(username='team1_user', password='password', team=team1)
        db.session.add(user)
        db.session.commit()
        print('Created team1_user')
"
```

### 3. Run Automated Tests

```bash
# Option A: Python script (more comprehensive)
python test_concurrent_users.py

# Option B: Simple bash script
./test_simple_concurrent.sh
```

### 4. Manual Browser Testing

**Test with multiple browser windows:**

1. **Chrome Normal** - Log in as User 1
   - Go to `http://localhost:8000/login`
   - Log in with first test user
   - Go to `/profile` and note the username/team

2. **Chrome Incognito** - Log in as User 2
   - Open incognito window (Ctrl+Shift+N)
   - Go to `http://localhost:8000/login`
   - Log in with second test user
   - Go to `/profile` and verify different user

3. **Firefox** - Log in as User 3
   - Open Firefox
   - Go to `http://localhost:8000/login`
   - Log in with third test user

**Then verify:**
- Each window shows only that user's data
- Refreshing one window doesn't affect others
- Each user sees their own team's services, not other teams'
- Scoreboard shows all teams but profile shows only your team

## What to Check

### ✓ Correct Behavior

- Each user only sees their own profile data
- Each user only sees their team's services
- Concurrent API calls work without errors
- No "DetachedInstanceError" or "ObjectDeletedError"
- No Flask context warnings

### ✗ Problems to Look For

#### Data Leakage
```
User A's window suddenly shows User B's username/team
→ This would indicate session contamination
```

#### Stale Data
```
- User A updates their service
- User B views services
- User B sees old data even after refresh
→ This would indicate improper session handling
```

#### Race Conditions
```
ERROR: DetachedInstanceError: Instance <Service at 0x...> is not bound to a Session
→ This means objects are being accessed outside their session
```

#### Context Issues
```
RuntimeError: Working outside of application context
→ Flask-SQLAlchemy requires app context for all DB operations
```

## Detailed Manual Test Scenarios

### Scenario 1: Concurrent Profile Views

**Setup:** 3 users logged in (different browsers)

1. All three users navigate to `/profile` simultaneously
2. Each should see only their own username and team
3. Refresh all three pages at the same time
4. Each should still see only their own data

**Expected:** No errors, no data mixing

### Scenario 2: Concurrent Service Updates

**Setup:** 2 users from different teams, both blue teams

1. User A updates their SSH service hostname
2. User B updates their SSH service hostname (different value)
3. Both users refresh their services page
4. Each sees only their team's SSH service with their hostname

**Expected:** No errors, changes isolated to each team

### Scenario 3: High Concurrency

**Setup:** 3 users logged in

1. Open browser dev tools (F12) → Network tab
2. Have all three users rapidly refresh the scoreboard (`/api/scoreboard`)
3. Click refresh about 10 times quickly on each browser
4. Check Network tab for any 500 errors

**Expected:** All requests return 200 OK, no server errors

### Scenario 4: Session Persistence

**Setup:** 1 user logged in

1. Log in as User A
2. Visit several pages (/profile, /services, /scoreboard)
3. Wait 30 seconds
4. Visit pages again
5. Check you're still logged in with correct user

**Expected:** Session persists, no re-login required, correct user data

## Monitoring Server Logs

Watch the server logs while testing:

```bash
# In another terminal
tail -f /var/log/scoring_engine.log  # or wherever logs go
```

Look for:
- ❌ Any warnings about detached instances
- ❌ SQLAlchemy "working outside application context" errors
- ❌ Exceptions related to sessions
- ✅ Normal request logs with 200 status codes

## Debugging Issues

If you find problems:

### Check Active Sessions

```python
from scoring_engine.web import create_app
from scoring_engine.db import db

app = create_app()
with app.app_context():
    # Check if there are orphaned sessions
    print(f"Session: {db.session}")
    print(f"Session registry: {db.session.registry()}")
```

### Verify Session Lifecycle

Add debug logging to see session creation/disposal:

```python
# In scoring_engine/web/__init__.py after db.init_app(app)

@app.before_request
def log_session_start():
    print(f"Request start - Session: {id(db.session)}")

@app.after_request
def log_session_end(response):
    print(f"Request end - Session: {id(db.session)}")
    return response
```

Each request should have a unique session ID.

## Performance Testing

Test that session management doesn't cause performance issues:

```bash
# Install apache bench if needed: apt-get install apache2-utils

# Test concurrent requests
ab -n 1000 -c 10 http://localhost:8000/api/overview

# Look for:
# - Mean time per request < 100ms
# - No failed requests
# - Requests per second > 50
```

## Success Criteria

✅ **Migration is successful if:**
- No data leakage between users
- No DetachedInstanceError exceptions
- All concurrent tests pass
- Manual testing shows proper isolation
- No performance degradation
- Sessions properly cleaned up (no memory leaks)

## Common Issues and Fixes

### Issue: "DetachedInstanceError"
**Cause:** Accessing model instances outside their session
**Fix:** Use `db.session.merge(obj)` or query fresh from database

### Issue: "Working outside application context"
**Cause:** Database access without Flask app context
**Fix:** Ensure all DB access is inside `with app.app_context():` or during request

### Issue: Stale data after updates
**Cause:** Session not committed or not refreshed
**Fix:** Ensure `db.session.commit()` after updates

### Issue: Session not found
**Cause:** Session removed before request completed
**Fix:** Don't manually call `db.session.remove()` during requests (Flask handles it)

## Additional Resources

- [Flask-SQLAlchemy Documentation](https://flask-sqlalchemy.palletsprojects.com/)
- [SQLAlchemy Session Basics](https://docs.sqlalchemy.org/en/14/orm/session_basics.html)
- [Testing Flask Applications](https://flask.palletsprojects.com/en/2.3.x/testing/)
