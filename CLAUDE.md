# CLAUDE.md - Scoring Engine

Python platform for Red/White/Blue team cybersecurity competitions.
Flask (web) + Celery (workers) + Redis (queue/cache) + MySQL/MariaDB (database).
Engine creates Round → queues Celery tasks → workers execute checks → results stored → cache updated.

## Critical Rules

### Client-Side Rendering via APIs
Pages MUST load dynamic content from cached JSON API endpoints (`/api/...`), NOT server-rendered Jinja templates. Data visibility varies by team role and ID — server-rendered pages risk serving one team's cached content to another.

- View: `return render_template("page.html")` — no DB queries
- Template: empty container + JS fetches `/api/...`
- API: `@cache.cached(make_cache_key=...)` with per-visibility key (`anonymous`, `white`, `red`, `team_5`)
- Cache flush: add helper to `cache_helper.py`, call after mutations

### Settings Cache
`Setting` model uses in-memory cache with 60s TTL. Always clear after modifying:
```python
setting = Setting.get_setting('sla_enabled')
setting.value = True
db.session.commit()
Setting.clear_cache('sla_enabled')  # Or Setting.clear_cache() for all
```

### Performance
Endpoints receive thousands of req/sec during competitions:
- Use JOINs, avoid N+1 queries
- Pre-fetch config before loops (no `get_sla_config()` in loops)
- Use custom ranking instead of external libraries

### Airgapped Deployments
Many competitions run offline. Use `./bin/create-airgapped-package.sh`. All deps must be in Docker images — no pip/apt/docker pull available.

## Structure

```
scoring_engine/
├── checks/           # Service check implementations (SSH, HTTP, DNS, etc.)
├── engine/           # Core: engine.py, basic_check.py, job.py (Celery tasks)
├── models/           # SQLAlchemy models
├── web/views/        # Flask views (HTML shells)
├── web/views/api/    # JSON API endpoints
├── sla.py            # SLA penalties and dynamic scoring
├── competition.py    # YAML competition definition parser
├── config_loader.py  # Priority: env vars → config file → defaults
└── cache_helper.py   # Redis cache invalidation helpers
tests/                # Mirrors main structure; use UnitTest base class
docker/               # Container build files
bin/                  # Entry points: setup, engine, web, worker
```

## Team Roles

- **White**: Organizers, full admin — `current_user.is_white_team`
- **Blue**: Defenders, own services/flags — `current_user.is_blue_team`
- **Red**: Attackers, agent checks — `current_user.is_red_team`

## DB Sessions

- **Engine**: `from scoring_engine.db import session` (manual)
- **Web**: Auto-managed per request (Flask-SQLAlchemy)
- **Tests**: `self.session` from `UnitTest` base class

## Adding a Service Check

Create `scoring_engine/checks/myservice.py` (auto-discovered):
```python
from scoring_engine.engine.basic_check import BasicCheck

class MyServiceCheck(BasicCheck):
    required_properties = ['username', 'password']
    CMD_TIMEOUT = 30

    def command_format(self, properties):
        return f'myservice-cli --host {self.host} --user {properties["username"]}'
```

## Config

Priority: `SCORINGENGINE_*` env vars → `SCORINGENGINE_CONFIG_FILE` → `engine.conf.inc` → defaults

- `SCORINGENGINE_OVERWRITE_DB=true` — reset database
- `SCORINGENGINE_EXAMPLE=true` — load example data

## Commands

```bash
docker compose up                              # Start all services
make run-tests                                 # Tests with coverage
make run-integration-tests                     # Integration tests (requires testbed)
pre-commit run --all-files                     # Lint (black, isort, flake8)
bump-my-version bump [patch|minor|major]       # Version bump
```

## Testing

All new code MUST have tests. Tests mirror `scoring_engine/` structure:
```python
from tests.scoring_engine.unit_test import UnitTest

class TestMyFeature(UnitTest):
    def test_something(self):
        pass  # self.session available for DB
```

## Complex Changes

For non-trivial work, use Architect → Implement → Review phases via Task tool.
Architect designs (read-only), Implementer codes to spec, Reviewer verifies.

## PRs

One feature per PR. Separate PRs are easier to review, test, and revert.

## Security

- Never log credentials in check output
- Validate all user input, check authorization (team role)
- Use SQLAlchemy ORM (parameterized queries)
