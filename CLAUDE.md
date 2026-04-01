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
alembic/                # Database migrations (Alembic)
├── versions/           # Migration scripts
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
tests/                # Mirrors main structure; plain classes + pytest fixtures
docker/               # Container build files
bin/                  # Entry points: setup, engine, web, worker, migrate
```

## Team Roles

- **White**: Organizers, full admin — `current_user.is_white_team`
- **Blue**: Defenders, own services/flags — `current_user.is_blue_team`
- **Red**: Attackers, agent checks — `current_user.is_red_team`

## DB Sessions

- **Engine**: `from scoring_engine.db import session` (manual)
- **Web**: Auto-managed per request (Flask-SQLAlchemy)
- **Tests**: `db.session` via autouse `db_session` fixture (see conftest.py)

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

## Dependencies

All dependencies are pinned to exact versions in `pyproject.toml`. When adding a new dependency, always use the **latest stable release** — check with `pip index versions <package>`. Pin to exact version (e.g., `"gevent==25.9.1"`, not `"gevent>=25"`).

## Database Migrations (Alembic)

Schema changes use Alembic for safe, versioned migrations.

```
alembic/
├── env.py              # Flask app context integration
├── script.py.mako      # Migration template
└── versions/           # Migration scripts (001_, 002_, ...)
```

**Key flows:**
- **Fresh install** (`bin/setup`): `create_all()` builds schema, then stamps Alembic to head — no migrations run
- **Upgrade existing DB** (`bin/migrate`): runs all pending Alembic migrations
- **Check for pending** (`bin/migrate --check`): exits 1 if migrations are pending (useful for CI)

**Creating a new migration:**
```bash
# Auto-generate from model changes (review the output!):
alembic revision --autogenerate -m "description of change"

# Or write manually:
alembic revision -m "description of change"
# Then edit alembic/versions/<rev>_description_of_change.py
```

**Migration best practices:**
- Always provide both `upgrade()` and `downgrade()`
- Use `batch_alter_table` for SQLite compatibility in tests
- Test migrations against both fresh DB (stamp) and existing DB (upgrade)
- Name files with sequential prefixes: `001_`, `002_`, etc.

**Helper functions** (in `scoring_engine/db.py`):
- `init_db()` — creates all tables + stamps Alembic head
- `run_migrations()` — runs `alembic upgrade head`
- `stamp_alembic_head()` — marks DB at latest revision without running migrations

## Commands

```bash
docker compose up                              # Start all services
python bin/migrate                             # Run pending DB migrations
python bin/migrate --check                     # Check for pending migrations
make run-tests                                 # Tests with coverage
make run-integration-tests                     # Integration tests (requires testbed)
pre-commit run --all-files                     # Lint (black, isort, flake8)
bump-my-version bump [patch|minor|major]       # Version bump
```

## Testing

All new code MUST have tests. Tests use plain classes with pytest fixtures (no base class inheritance).

**Model/logic tests** — just need `db_session` (autouse, no explicit request needed):
```python
from scoring_engine.db import db
from scoring_engine.models.team import Team

class TestMyFeature:
    def test_something(self):
        team = Team(name="Test", color="Blue")
        db.session.add(team)
        db.session.commit()
        assert team.id is not None
```

**Web/API tests** — request the `test_client` fixture:
```python
import pytest
from scoring_engine.db import db
from scoring_engine.models.team import Team
from scoring_engine.models.user import User

class TestMyView:
    @pytest.fixture(autouse=True)
    def setup(self, test_client, db_session):
        self.client = test_client

    def test_requires_auth(self):
        resp = self.client.get("/my-route")
        assert resp.status_code == 302
```

**Key fixtures** (defined in `tests/scoring_engine/conftest.py`):
- `db_session` — autouse, provides clean DB per test (DELETE all rows + re-insert settings)
- `test_client` — Flask test client with CSRF disabled
- `three_teams` — creates White/Blue/Red teams with users (password: `"testpass"`)
- `white_login`, `blue_login`, `red_login` — logged-in client + teams dict
- `_login(client, username)` — helper to POST /login

## Complex Changes

For non-trivial work, use Architect → Implement → Review phases via Task tool.
Architect designs (read-only), Implementer codes to spec, Reviewer verifies.

## PRs

One feature per PR. Separate PRs are easier to review, test, and revert.

## Security

- Never log credentials in check output
- Validate all user input, check authorization (team role)
- Use SQLAlchemy ORM (parameterized queries)
