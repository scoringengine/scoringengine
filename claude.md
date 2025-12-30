# Claude.md - AI Model Guide for Scoring Engine

This guide helps Claude and other AI models navigate and understand the Scoring Engine codebase effectively.

## Project Overview

Scoring Engine is a Python-based platform for running Red/White/Blue team cybersecurity competitions. It:
- Automates service availability checks each round
- Provides a web interface for scoreboard and configuration
- Uses Celery workers with Redis for parallel check execution
- Stores data in MySQL/MariaDB using SQLAlchemy ORM
- Built with Flask for the web application

## Codebase Structure

```
scoringengine/
├── scoring_engine/          # Main application code
│   ├── checks/              # Service check implementations (SSH, HTTP, DNS, etc.)
│   ├── engine/              # Core engine logic for running competitions
│   ├── models/              # SQLAlchemy database models
│   ├── web/                 # Flask web application
│   │   ├── views/           # View controllers (both HTML and API)
│   │   │   └── api/         # JSON API endpoints
│   │   ├── templates/       # Jinja2 HTML templates
│   │   └── static/          # CSS, JavaScript, images
│   ├── competition.py       # Competition YAML parsing and loading
│   ├── config_loader.py     # Configuration file and environment variable handling
│   ├── cache_helper.py      # Redis caching utilities
│   └── celery_app.py        # Celery task queue configuration
├── tests/                   # Test suite
│   ├── scoring_engine/      # Unit tests mirroring main structure
│   └── integration/         # Integration tests
├── docker/                  # Docker build files for each service
│   ├── base/                # Base image with dependencies
│   ├── engine/              # Competition engine container
│   ├── web/                 # Web UI container
│   ├── worker/              # Celery worker container
│   └── testbed/             # Test services for checks
├── bin/                     # Helper scripts and entry points
├── configs/                 # Sample configuration files
└── docs/                    # Sphinx documentation source

```

## Key Components

### 1. Database Models (`scoring_engine/models/`)

All models inherit from `Base` and use SQLAlchemy ORM:

- **team.py**: Teams competing in the event (Red, Blue, White teams)
- **user.py**: User accounts with role-based permissions
- **service.py**: Services to be checked (e.g., web server, SSH, DNS)
- **check.py**: Individual check results (pass/fail/timeout)
- **round.py**: Competition rounds
- **account.py**: Service credentials for checks
- **environment.py**: Key-value pairs for service configuration
- **property.py**: Additional service properties
- **flag.py**: Capture-the-flag style flags teams can capture
- **inject.py**: Manual tasks/challenges for teams
- **setting.py**: Global competition settings

**Key pattern**: Models are located in individual files, imported via `models/__init__.py`

### 2. Service Checks (`scoring_engine/checks/`)

Each check is a Python class that verifies a service is working correctly:

- Inherit from `BasicCheck` (defined in `engine/basic_check.py`)
- Implement `command_format()` to return check logic
- Support properties via `self.properties` dictionary
- Common checks: http, https, ssh, ftp, smtp, dns, icmp, mysql, postgresql, ldap, smb
- Custom checks in `checks/bin/` for complex scenarios

**Example check structure**:
```python
from scoring_engine.engine.basic_check import BasicCheck

class SSHCheck(BasicCheck):
    required_properties = ['username', 'password']
    CMD = 'sshpass -p {password} ssh ...'
```

### 3. Competition Engine (`scoring_engine/engine/`)

Core scheduling and execution logic:

- **engine.py**: Main `Engine` class that orchestrates rounds
  - `load_checks()`: Dynamically imports check modules
  - `run()`: Main loop that runs rounds on schedule
  - Uses Celery for distributed check execution

- **basic_check.py**: Base class for all service checks
  - Defines check interface and common functionality
  - Returns: `CHECK_SUCCESS_TEXT`, `CHECK_FAILURE_TEXT`, or `CHECK_TIMED_OUT_TEXT`

- **execute_command.py**: Shell command execution with timeout

- **job.py**: Celery job definition

### 4. Web Application (`scoring_engine/web/`)

Flask application with blueprints:

- **views/**: View controllers organized by function
  - `admin.py`: Competition management (White Team)
  - `auth.py`: Login/logout
  - `scoreboard.py`: Public scoreboard
  - `overview.py`: Team overview dashboard
  - `services.py`: Service management
  - `api/`: JSON API endpoints for programmatic access

- **templates/**: Jinja2 HTML templates
- **static/**: Frontend assets

### 5. Configuration (`config_loader.py`, `engine.conf.inc`)

Configuration priority (highest to lowest):
1. Environment variables (e.g., `SCORINGENGINE_DB_HOST`)
2. Config file specified by `SCORINGENGINE_CONFIG_FILE`
3. Default `engine.conf.inc` in working directory
4. Built-in defaults

**Important config sections**:
- `[MysqlConfig]`: Database connection
- `[RedisConfig]`: Cache and Celery broker
- `[Checks]`: Location of check modules
- `[Competition]`: Competition YAML file path

### 6. Competition Definition (`competition.py`)

Competitions are defined in YAML files with:
- Teams and users
- Services per team
- Service accounts and properties
- Validation logic in `Competition` class

## Common Tasks

### Finding Where Something Happens

**Service checks are executed**:
- Entry point: `engine/engine.py:run()`
- Celery task: `engine/job.py`
- Actual execution: Check classes in `checks/`

**Scores are calculated**:
- Check results stored: `models/check.py`
- Team scoring: View logic in `web/views/scoreboard.py` and `web/views/api/overview.py`

**Web pages are rendered**:
- Routes defined: `web/views/` files with `@mod.route()` decorators
- Templates: `web/templates/` directory
- Template inheritance: Check `base.html` for common layout

**Database queries**:
- Models define relationships and queries
- Use `session.query()` for complex queries
- Example: `Team.query.filter_by(name='Team1').first()`

### Adding a New Service Check

1. Create `scoring_engine/checks/myservice.py`
2. Inherit from `BasicCheck` or `HTTPPostCheck`
3. Define `required_properties` list
4. Implement `command_format()` method
5. Add test in `tests/scoring_engine/checks/test_myservice.py`
6. Checks are auto-discovered by `Engine.load_check_files()`

### Modifying the Web Interface

1. Routes: Edit or add to `web/views/*.py`
2. Templates: Modify `web/templates/*.html`
3. API endpoints: Add to `web/views/api/*.py`
4. Frontend assets: Update `web/static/`

### Database Schema Changes

1. Modify models in `scoring_engine/models/`
2. Generate migration (currently manual - check existing patterns)
3. Test with `SCORINGENGINE_OVERWRITE_DB=true` for fresh DB

## Development Workflow

### Running Locally

```bash
# Start all services
docker-compose build
docker-compose up

# Run with example data
SCORINGENGINE_EXAMPLE=true docker-compose up

# Reset database
SCORINGENGINE_OVERWRITE_DB=true docker-compose up
```

Access at http://localhost with credentials from README.md

### Airgapped/Offline Deployments

**IMPORTANT**: Many competitions run in completely airgapped environments with NO internet access.

For airgapped deployments, ALL dependencies must be vendored before entering the environment:

**Required vendoring**:
- Docker images (base Python, Redis, MariaDB, Nginx)
- Python packages (all pip dependencies)
- System packages (all apt dependencies)
- Application images (scoringengine/base, engine, worker, web, bootstrap)

**Preparation workflow** (with internet):
1. Build all images: `docker-compose build --no-cache`
2. Export images: `docker save [image] -o [file].tar`
3. Package with repository code
4. Transfer to airgapped environment

**Deployment workflow** (airgapped):
1. Load images: `docker load -i [file].tar`
2. Deploy: `docker-compose up -d`

**Key principle**: Once images are built and loaded, NO external network access is required. All dependencies are embedded in the Docker image layers.

See `docs/source/installation/airgapped.rst` for complete step-by-step guide.

### Running Tests

```bash
# Unit tests
pytest tests/

# With coverage
make run-tests

# Integration tests (requires testbed)
make run-integration-tests

# Specific test file
pytest tests/scoring_engine/test_competition.py

# Specific test function
pytest tests/scoring_engine/test_competition.py::test_function_name
```

### Code Quality

```bash
# Run pre-commit hooks (flake8, etc.)
pre-commit run --files <changed-files>

# Check all files
pre-commit run --all-files
```

**Style notes**:
- Follow PEP 8
- Max line length: 160 characters (see `.flake8`)
- Use descriptive variable names
- Add docstrings for complex functions

## Testing Patterns

Tests mirror the main code structure:

- `tests/scoring_engine/models/` - Model tests
- `tests/scoring_engine/checks/` - Check tests
- `tests/scoring_engine/web/` - Web view tests
- `tests/scoring_engine/engine/` - Engine tests

**Common test utilities**:
- `tests/scoring_engine/helpers.py`: Test fixtures and helpers
- `tests/conftest.py`: Pytest configuration and fixtures
- Use `@pytest.fixture` for reusable test data

**Testing checks**:
```python
# Mock service responses
# Test required_properties validation
# Test command_format() output
# Test both success and failure cases
```

## Architecture Patterns

### Celery Task Queue

- Workers execute checks in parallel
- Broker: Redis
- Task definition: `engine/job.py`
- Worker startup: `docker/worker/`

### Caching Strategy

- Cache layer: Redis (via Flask-Caching)
- Helper: `cache_helper.py:update_all_cache()`
- Cached data: Scoreboard, team stats, round info
- Invalidation: After each round completion

### Database Sessions

- Global session: `db.py:session`
- Web requests: Auto-managed by Flask-SQLAlchemy
- Engine: Manual session management in `engine/engine.py`

### Dynamic Module Loading

Checks are loaded dynamically:
```python
# engine/engine.py
@staticmethod
def load_check_files(checks_location):
    # Scans directory for Python files
    # Imports modules dynamically
    # Returns list of check classes
```

## Important Files to Know

- **engine.conf.inc**: Default configuration template
- **docker-compose.yml**: Service orchestration
- **setup.py** / **pyproject.toml**: Python package definition and dependencies
- **Makefile**: Common commands for build/test/run
- **.flake8**: Linter configuration
- **requirements files**: In docker/*/requirements.txt

## Security Considerations

This is a competition platform handling:
- User authentication (bcrypt password hashing)
- Service credentials (stored in database)
- Team isolation (authorization checks in views)
- Flag verification (crypto tokens)

**When modifying**:
- Validate user input
- Check authorization (e.g., `@login_required`, team membership)
- Sanitize service check outputs
- Don't log sensitive credentials

## Common Pitfalls

1. **Check timeouts**: Service checks have timeout limits (see `execute_command.py`)
2. **Database session management**: Ensure proper commit/rollback
3. **Circular imports**: Models import each other - be careful with imports
4. **Config precedence**: Environment variables override config file
5. **Docker networking**: Services communicate via service names (e.g., `redis`, `mysql`)

## Helpful Commands

```bash
# View logs
docker-compose logs -f [service]

# Access database
docker-compose exec mysql mysql -u scoring_engine -p scoringengine

# Access Redis CLI
docker-compose exec redis redis-cli

# Restart specific service
docker-compose restart [web|engine|worker]

# Run shell in container
docker-compose exec web bash
```

## Documentation

- Full docs: https://scoringengine.readthedocs.io/
- Local docs: `make -C docs html` then open `docs/build/html/index.html`
- API docs: Check docstrings in code

## Quick Reference: File Locations

| Need to... | Look in... |
|------------|-----------|
| Add service check | `scoring_engine/checks/` |
| Modify database schema | `scoring_engine/models/` |
| Change web UI | `scoring_engine/web/views/` and `templates/` |
| Update API | `scoring_engine/web/views/api/` |
| Fix check execution | `scoring_engine/engine/` |
| Adjust configuration | `config_loader.py`, `engine.conf.inc` |
| Add dependencies | `pyproject.toml` |
| Modify Docker setup | `docker/` and `docker-compose.yml` |
| Update tests | `tests/scoring_engine/` (mirrors main structure) |

---

**Note**: This codebase follows a straightforward architecture. When in doubt:
1. Check existing patterns in similar files
2. Read the model definitions to understand data structure
3. Follow the code path from web route → model → database
4. Look at tests for usage examples
