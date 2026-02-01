# CLAUDE.md - Scoring Engine

## Project Overview

**Scoring Engine**: Python platform for Red/White/Blue team cybersecurity competitions.

**Architecture**: Flask (web) + Celery (workers) + Redis (queue/cache) + MySQL/MariaDB (database)

**Key Flow**: Engine creates Round → queues Celery tasks → workers execute service checks → results stored → cache updated

## Critical Gotchas

### Settings Cache (IMPORTANT)
The `Setting` model uses in-memory cache with 60-second TTL. **ALWAYS clear cache after modifying settings**:
```python
setting = Setting.get_setting('sla_enabled')
setting.value = True
db.session.commit()
Setting.clear_cache('sla_enabled')  # Or Setting.clear_cache() for all
```
In tests, always call `Setting.clear_cache()` before assertions.

### Performance (Competition Critical)
During competitions, endpoints receive thousands of requests/second:
- Use JOINs, avoid N+1 queries
- Pre-fetch config values before loops (don't call `get_sla_config()` in loops)
- Use custom ranking instead of external libraries

### Airgapped Deployments
Many competitions run offline. Use `./bin/create-airgapped-package.sh` to package everything. All dependencies must be in Docker images - no pip/apt/docker pull available.

## Repository Structure

```
scoring_engine/
├── checks/           # Service check implementations (28 checks: SSH, HTTP, DNS, etc.)
├── engine/           # Core engine: engine.py, basic_check.py, job.py (Celery tasks)
├── models/           # SQLAlchemy models: team, user, service, check, round, setting, etc.
├── web/
│   ├── views/        # Flask views (HTML)
│   └── views/api/    # JSON API endpoints
├── sla.py            # SLA penalties and dynamic scoring
├── competition.py    # YAML parsing for competition definition
├── config_loader.py  # Config priority: env vars → config file → defaults
└── cache_helper.py   # Redis caching utilities

tests/                # Mirrors main structure; use UnitTest base class
docker/               # Container build files
bin/                  # Entry points: setup, engine, web, worker
```

## Adding a Service Check

Create `scoring_engine/checks/myservice.py`:
```python
from scoring_engine.engine.basic_check import BasicCheck

class MyServiceCheck(BasicCheck):
    required_properties = ['username', 'password']
    CMD_TIMEOUT = 30

    def command_format(self, properties):
        return f'myservice-cli --host {self.host} --user {properties["username"]}'
```
Checks auto-discovered from `checks/` directory. Add test in `tests/scoring_engine/checks/`.

## Database Sessions

- **Engine**: Manual via `from scoring_engine.db import session`
- **Web**: Auto-managed per request via Flask-SQLAlchemy
- **Tests**: Use `self.session` from `UnitTest` base class

## Team Roles

- **White Team**: Competition organizers (full admin access)
- **Blue Team**: Defenders (view own services, submit flags)
- **Red Team**: Attackers (agent checks, different scoring)

Check with `current_user.is_white_team`, `is_blue_team`, `is_red_team`.

## Configuration

Priority: `SCORINGENGINE_*` env vars → `SCORINGENGINE_CONFIG_FILE` → `engine.conf.inc` → defaults

Key env vars:
- `SCORINGENGINE_OVERWRITE_DB=true`: Reset database
- `SCORINGENGINE_EXAMPLE=true`: Load example data

## Development Commands

```bash
docker compose up                    # Start all services
make run-tests                       # Run tests with coverage
pre-commit run --all-files           # Lint (black, isort, flake8)
bump-my-version bump [patch|minor|major]  # Version bump
```

## Key Files

| Task | Location |
|------|----------|
| Add check | `scoring_engine/checks/` |
| Database model | `scoring_engine/models/` |
| Web view/API | `scoring_engine/web/views/` or `views/api/` |
| SLA/scoring logic | `scoring_engine/sla.py` |
| Config | `config_loader.py`, `engine.conf.inc` |

## Testing

All new code MUST have tests. Tests in `tests/scoring_engine/` mirror main structure.

```python
from tests.scoring_engine.unit_test import UnitTest

class TestMyFeature(UnitTest):
    def test_something(self):
        # self.session available for DB access
        pass
```

Integration tests: `make run-integration-tests` (requires testbed services)

## Pull Request Guidelines

**One feature per PR**: Always create separate branches and PRs for each distinct feature. Avoid "mono PRs" that combine multiple unrelated features.

Good:
- `feature/mobile-responsive-scoreboard` - only CSS changes for mobile
- `feature/fog-of-war` - only fog of war logic
- `feature/webhooks` - only webhook notifications

Bad:
- Single PR with mobile CSS + fog of war + webhooks + new scoring system

**Reasoning**: Separate PRs are easier to review, test, revert, and discuss. If one feature needs changes, it doesn't block others.

## Security Checklist

- Never log credentials in check output
- Validate all user input
- Check authorization (team membership, role)
- Use SQLAlchemy ORM (parameterized queries)
