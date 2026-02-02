# CLAUDE.md - Scoring Engine

Cybersecurity competition platform: Flask web UI + Celery workers + MySQL + Redis cache.

## Critical Rules

**MUST follow these rules:**
- All new code MUST have tests
- Run `pre-commit run --files <changed-files>` before committing
- After modifying `Setting` values, ALWAYS call `Setting.clear_cache()` (60s TTL otherwise)
- Never log credentials in check output
- Never push to master without PR
- Airgapped deployments: ALL dependencies must be vendored (no pip/apt/docker pull at runtime)

**DO NOT:**
- Create documentation files unless asked
- Add features not requested
- Refactor code unnecessarily
- Add backwards-compatibility hacks or abstractions for one-time use

## Project Structure

```
scoring_engine/
├── checks/           # Service check plugins (auto-discovered)
├── engine/           # Competition orchestration
│   ├── engine.py     # Main loop, round management
│   ├── basic_check.py # Check base class
│   └── job.py        # Celery task definitions
├── models/           # SQLAlchemy models
│   └── setting.py    # Uses in-memory cache - MUST clear after updates
├── web/
│   ├── views/        # HTML views
│   └── views/api/    # JSON API endpoints
├── sla.py            # SLA penalties and dynamic scoring
└── competition.py    # YAML parsing
tests/                # Mirrors main structure
docker/               # Container build files
```

## Key Patterns

### Adding a Service Check

Checks auto-discovered from `scoring_engine/checks/`. No registration needed.

```python
# scoring_engine/checks/myservice.py
from scoring_engine.engine.basic_check import BasicCheck

class MyServiceCheck(BasicCheck):
    required_properties = ['username', 'password']
    CMD_TIMEOUT = 30

    def command_format(self, properties):
        return f"myservice-cli --host {self.host} --user {properties['username']}"
```

```python
# tests/scoring_engine/checks/test_myservice.py
def test_myservice_command_format():
    check = MyServiceCheck('192.168.1.1', 1234, {'username': 'admin', 'password': 'secret'})
    assert 'myservice-cli' in check.command_format(check.properties)
```

### Settings Cache (Critical)

```python
from scoring_engine.models.setting import Setting

# Get (auto-cached 60s)
value = Setting.get_setting('setting_name').value

# Update - MUST clear cache!
setting = Setting.get_setting('sla_enabled')
setting.value = True
db.session.commit()
Setting.clear_cache()  # Or Setting.clear_cache('sla_enabled')
```

### Team Roles

| Role | Access |
|------|--------|
| White Team | Full admin, manage competition |
| Blue Team | View own services, submit flags |
| Red Team | Agent checks, different scoring |

```python
# Check in views
if current_user.is_white_team: ...
elif current_user.is_blue_team: ...
```

### Database Sessions

- **Engine/Workers**: Manual via `from scoring_engine.db import session`
- **Web**: Auto-managed per request via Flask-SQLAlchemy
- **Tests**: Use `self.session` from `UnitTest` base class

## Configuration

Priority: env vars > config file > `engine.conf.inc` > defaults

| Env Variable | Purpose |
|--------------|---------|
| `SCORINGENGINE_OVERWRITE_DB=true` | Reset database on startup |
| `SCORINGENGINE_EXAMPLE=true` | Load example data |
| `SCORINGENGINE_DEBUG=true` | Enable debug mode |
| `SCORINGENGINE_CONFIG_FILE` | Path to config file |

## Competition YAML

```yaml
teams:
  - name: Team 1
    color: blue
    users:
      - username: user1
        password: pass1
    services:
      - name: Web Server
        check_name: HTTP  # Matches class name in checks/
        host: 192.168.1.10
        port: 80
        points: 100
        properties:
          - name: url_path
            value: /index.html
```

## Performance

High-traffic endpoints during competitions - optimize queries:

```python
# BAD: N+1
for service in services:
    checks = Check.query.filter_by(service_id=service.id).all()

# GOOD: Single JOIN query
data = db.session.query(Service.team_id, Check.result).join(Check).all()
```

**Anti-patterns:**
- Querying inside loops
- Calling `get_sla_config()` repeatedly in loops
- Loading full objects when only IDs needed
- Forgetting `Setting.clear_cache()` after updates

## Security

- Never log credentials/passwords
- Validate all user input
- Check team authorization (`current_user.is_white_team`, etc.)
- Sanitize check output before display

## Commands

| Task | Command |
|------|---------|
| Run | `docker compose up` or `make run` |
| Run with demo data | `SCORINGENGINE_EXAMPLE=true docker compose up` |
| Reset DB | `SCORINGENGINE_OVERWRITE_DB=true docker compose up` |
| Test | `pytest tests/` or `make run-tests` |
| Lint | `pre-commit run --files <files>` |
| Bump version | `bump-my-version bump [patch\|minor\|major]` |
| Airgapped package | `./bin/create-airgapped-package.sh` |

## File Locations

| Task | Location |
|------|----------|
| Add service check | `scoring_engine/checks/` |
| Database models | `scoring_engine/models/` |
| Web views | `scoring_engine/web/views/` |
| API endpoints | `scoring_engine/web/views/api/` |
| Templates | `scoring_engine/web/templates/` |
| Engine logic | `scoring_engine/engine/` |
| SLA/scoring | `scoring_engine/sla.py` |
| Tests | `tests/scoring_engine/` (mirrors main) |
| Config | `engine.conf.inc`, `config_loader.py` |
| Dependencies | `pyproject.toml` |
| Docker | `docker/`, `docker-compose.yml` |
| CI/CD | `.github/workflows/` |

## Testing

```bash
pytest tests/                                    # All tests
pytest tests/scoring_engine/checks/test_ssh.py  # Specific file
pytest -k "test_check"                           # Pattern match
make run-integration-tests                       # Integration (needs testbed)
```

Test base class provides `self.session`:
```python
from tests.scoring_engine.unit_test import UnitTest

class TestMyFeature(UnitTest):
    def test_something(self):
        # self.session available for DB operations
        pass
```
