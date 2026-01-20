# CLAUDE.md - AI Assistant Guide for Scoring Engine

This guide helps AI assistants (like Claude) navigate and understand the Scoring Engine codebase effectively. It provides comprehensive information about architecture, conventions, and development workflows.

## Project Overview

**Scoring Engine** is a Python-based platform for running Red/White/Blue team cybersecurity competitions. It:
- Automates service availability checks each round
- Provides a web interface for scoreboard and team management
- Uses Celery workers with Redis for distributed parallel check execution
- Stores data in MySQL/MariaDB using SQLAlchemy ORM
- Built with Flask for the web application layer

**Key Architecture**: Distributed task queue (Celery) + Web UI (Flask) + Database (MySQL/MariaDB) + Cache (Redis)

## Repository Structure

```
scoringengine/
├── scoring_engine/          # Main application code
│   ├── checks/              # Service check implementations (SSH, HTTP, DNS, etc.)
│   │   └── bin/             # Complex check scripts
│   ├── engine/              # Core engine logic for running competitions
│   │   ├── engine.py        # Main Engine class and orchestration
│   │   ├── basic_check.py   # Base class for all checks
│   │   ├── http_post_check.py # HTTP POST check base class
│   │   ├── job.py           # Celery task definitions
│   │   └── execute_command.py # Shell command execution with timeout
│   ├── models/              # SQLAlchemy database models
│   │   ├── team.py          # Team management
│   │   ├── user.py          # User accounts and authentication
│   │   ├── service.py       # Service definitions
│   │   ├── check.py         # Check results
│   │   ├── round.py         # Competition rounds
│   │   ├── account.py       # Service credentials
│   │   ├── environment.py   # Environment variables for services
│   │   ├── property.py      # Service properties
│   │   ├── flag.py          # CTF flags
│   │   ├── inject.py        # Manual tasks/challenges
│   │   ├── setting.py       # Global settings (cached)
│   │   └── notifications.py # Team notifications
│   ├── web/                 # Flask web application
│   │   ├── views/           # View controllers (HTML and API)
│   │   │   ├── admin.py     # White team administration
│   │   │   ├── auth.py      # Authentication (login/logout)
│   │   │   ├── scoreboard.py # Public scoreboard
│   │   │   ├── overview.py  # Team dashboard
│   │   │   ├── services.py  # Service management
│   │   │   ├── flags.py     # Flag submission
│   │   │   ├── injects.py   # Inject management
│   │   │   └── api/         # JSON API endpoints
│   │   │       ├── admin.py # Admin API
│   │   │       ├── agent.py # Red team agent API
│   │   │       ├── overview.py # Overview API
│   │   │       ├── profile.py # User profile API
│   │   │       ├── scoreboard.py # Scoreboard API
│   │   │       ├── service.py # Service API
│   │   │       ├── team.py  # Team API
│   │   │       ├── stats.py # Statistics API
│   │   │       ├── flags.py # Flags API
│   │   │       ├── injects.py # Injects API
│   │   │       └── notifications.py # Notifications API
│   │   ├── templates/       # Jinja2 HTML templates
│   │   └── static/          # CSS, JavaScript, images
│   ├── competition.py       # Competition YAML parsing and validation
│   ├── config_loader.py     # Configuration file and environment variable handling
│   ├── cache_helper.py      # Redis caching utilities
│   ├── celery_app.py        # Celery task queue configuration
│   ├── celery_stats.py      # Celery worker statistics
│   ├── db.py                # Database session management
│   ├── config.py            # Configuration object
│   ├── cache.py             # Flask-Caching setup
│   ├── logger.py            # Logging configuration
│   └── version.py           # Version information
├── tests/                   # Test suite
│   ├── scoring_engine/      # Unit tests (mirrors main structure)
│   │   ├── checks/          # Check tests
│   │   ├── models/          # Model tests
│   │   ├── engine/          # Engine tests
│   │   └── web/             # Web tests
│   ├── integration/         # Integration tests (require live services)
│   ├── conftest.py          # Pytest configuration and fixtures
│   ├── helpers.py           # Test helper functions
│   └── requirements.txt     # Test dependencies
├── docker/                  # Docker build files for each service
│   ├── base/                # Base image with Python dependencies
│   ├── bootstrap/           # Database initialization
│   ├── engine/              # Competition engine container
│   ├── nginx/               # Nginx reverse proxy configuration
│   ├── tester/              # Test runner container
│   ├── web/                 # Web UI container
│   ├── worker/              # Celery worker container
│   └── testbed/             # Test services for integration tests
├── bin/                     # Helper scripts and entry points
│   ├── setup                # Initial setup script
│   ├── engine               # Engine entry point
│   ├── web                  # Web entry point
│   ├── worker               # Worker entry point
│   ├── competition.yaml     # Example competition definition
│   └── create-airgapped-package.sh # Airgapped deployment packager
├── configs/                 # Sample configuration files
├── docs/                    # Sphinx documentation source
│   └── source/
│       ├── installation/    # Installation guides
│       │   └── airgapped.rst # Airgapped deployment guide
│       └── checks/          # Check documentation
├── .github/                 # GitHub Actions workflows
│   └── workflows/
│       ├── tests.yml        # CI testing
│       ├── publish-images.yml # Docker image publishing
│       ├── codeql.yml       # Security analysis
│       └── snyk-container-analysis.yml # Container security
├── engine.conf.inc          # Default configuration template
├── docker-compose.yml       # Service orchestration
├── pyproject.toml           # Python package definition and dependencies
├── setup.py                 # Legacy setup script
├── Makefile                 # Common commands for build/test/run
├── .pre-commit-config.yaml  # Pre-commit hooks (black, isort, flake8)
├── .flake8                  # Linter configuration
├── .bumpversion.cfg         # Version bumping configuration
├── README.md                # Project README
├── VERSION_MANAGEMENT.md    # Version management guide
├── AGENTS.md                # Basic agent guidelines
└── claude.md                # Previous AI assistant guide (lowercase)
```

## Key Components Deep Dive

### 1. Database Models (`scoring_engine/models/`)

All models inherit from `Base` (SQLAlchemy declarative base) and follow these patterns:

**Core Models:**
- **base.py**: SQLAlchemy declarative base class
- **team.py**: Teams competing (Red, Blue, White teams with different roles)
- **user.py**: User accounts with bcrypt password hashing and role-based permissions
- **service.py**: Services to be checked (web servers, SSH, DNS, etc.)
- **check.py**: Individual check results (pass/fail/timeout with timestamps)
- **round.py**: Competition rounds with number tracking
- **account.py**: Service credentials for authentication checks
- **environment.py**: Key-value environment variables for services
- **property.py**: Additional service properties (flexible key-value pairs)
- **flag.py**: CTF-style flags that teams can capture
- **inject.py**: Manual tasks/challenges for teams with scoring
- **setting.py**: Global competition settings (uses caching via `@cached_property`)
- **notifications.py**: Team notifications and messaging
- **kb.py**: Knowledge base entries
- **agent.py**: Red team agent tracking

**Important Patterns:**
- Models use SQLAlchemy relationships with `back_populates`
- Lazy loading: `lazy='dynamic'` for collections
- Settings model has caching: `Setting.get_setting()` with Redis cache
- All timestamps use `db.DateTime` with `default=datetime.utcnow`

### 2. Service Checks (`scoring_engine/checks/`)

Each check is a Python class that verifies service functionality:

**Available Checks (28 total):**
- Network: `icmp.py`, `dns.py`, `nfs.py`
- Web: `http.py`, `https.py`, `elasticsearch.py`, `wordpress.py`, `webapp_*.py`
- Auth: `ssh.py`, `telnet.py`, `ldap.py`, `winrm.py`
- File Transfer: `ftp.py`, `smb.py`
- Email: `smtp.py`, `smtps.py`, `imap.py`, `imaps.py`, `pop3.py`, `pop3s.py`
- Database: `mysql.py`, `postgresql.py`, `mssql.py`
- Remote Desktop: `rdp.py`, `vnc.py`
- VPN: `openvpn.py`
- Custom: `agent.py` (Red team agent checks)

**Check Structure Pattern:**
```python
from scoring_engine.engine.basic_check import BasicCheck

class ExampleCheck(BasicCheck):
    # Required properties that must be defined in competition.yaml
    required_properties = ['username', 'password']

    # Optional: Default timeout
    CMD_TIMEOUT = 30

    def command_format(self, properties):
        """
        Returns the shell command to execute for this check.

        Args:
            properties: Dict of service properties from competition.yaml

        Returns:
            String command to execute
        """
        # Access self.host, self.port, properties dict
        return 'command --host {host} --port {port}'.format(
            host=self.host,
            port=self.port
        )
```

**Check Execution Flow:**
1. Engine loads check class dynamically from `checks/` directory
2. Instantiates check with service parameters (host, port, properties)
3. Calls `command_format()` to get shell command
4. Executes command via `execute_command.py` with timeout
5. Parses output for success/failure keywords
6. Stores result in database as `Check` model

**Return Values:**
- `CHECK_SUCCESS_TEXT` (defined in check class or default)
- `CHECK_FAILURE_TEXT` (from stderr or exception)
- `CHECK_TIMED_OUT_TEXT` (timeout exceeded)

### 3. Competition Engine (`scoring_engine/engine/`)

**engine.py** - Main orchestration:
```python
class Engine:
    def __init__(self):
        # Load configuration
        # Connect to database
        # Load checks from filesystem

    def load_check_files(self, checks_location):
        # Dynamically import all Python files in checks/
        # Return list of check classes

    def run(self):
        # Main loop:
        # 1. Create new Round
        # 2. For each team's services:
        #    - Queue Celery task (job.py)
        # 3. Wait for round completion
        # 4. Update cache
        # 5. Sleep until next round
```

**basic_check.py** - Base class providing:
- Command execution framework
- Timeout handling
- Success/failure detection
- Property validation

**http_post_check.py** - Specialized base for HTTP POST checks

**job.py** - Celery task definition:
```python
@celery_app.task
def execute_check(check_obj):
    # Execute service check
    # Store result in database
    # Return status
```

**execute_command.py** - Shell command execution with:
- Subprocess management
- Timeout enforcement
- Output capture (stdout/stderr)
- Error handling

### 4. Web Application (`scoring_engine/web/`)

Flask application with blueprints for different sections:

**View Organization:**
- **HTML Views** (`views/*.py`): Render Jinja2 templates
  - `admin.py`: White team competition management
  - `auth.py`: Login/logout/session management
  - `scoreboard.py`: Public scoreboard display
  - `overview.py`: Team-specific dashboard
  - `services.py`: Service status and management
  - `flags.py`: Flag submission interface
  - `injects.py`: Inject/task management
  - `welcome.py`: Landing page
  - `about.py`: About page
  - `profile.py`: User profile
  - `stats.py`: Statistics pages
  - `notifications.py`: Notification center

- **API Views** (`views/api/*.py`): JSON endpoints
  - All return `jsonify()` responses
  - Support pagination where applicable
  - Include error handling with appropriate HTTP status codes
  - Authentication via Flask-Login

**Template Structure:**
- `base.html`: Common layout with navbar, footer
- Templates use Jinja2 inheritance: `{% extends "base.html" %}`
- Static files in `static/`: CSS, JS, images

**Authentication:**
- Flask-Login for session management
- `@login_required` decorator for protected routes
- Role-based access: `current_user.is_white_team`, `current_user.is_blue_team`, etc.

### 5. Configuration System

**Priority Order (highest to lowest):**
1. Environment variables: `SCORINGENGINE_*` (e.g., `SCORINGENGINE_DB_HOST`)
2. Config file: Path specified by `SCORINGENGINE_CONFIG_FILE` env var
3. Default config: `engine.conf.inc` in current directory
4. Built-in defaults in `config_loader.py`

**Configuration Sections:**
```ini
[MysqlConfig]
host = mysql
port = 3306
username = scoring_engine
password = password
database = scoringengine

[RedisConfig]
host = redis
port = 6379
password =

[Checks]
location = scoring_engine/checks

[Competition]
yaml_file = competition.yaml
```

**Important Environment Variables:**
- `SCORINGENGINE_OVERWRITE_DB=true`: Reset database on startup
- `SCORINGENGINE_EXAMPLE=true`: Load example data
- `SCORINGENGINE_DEBUG=true`: Enable debug mode
- `SCORINGENGINE_VERSION`: Git hash for version tracking

### 6. Competition Definition (`competition.py`)

Competitions defined in YAML with structure:
```yaml
teams:
  - name: Team 1
    color: blue
    users:
      - username: user1
        password: pass1
    services:
      - name: Web Server
        check_name: HTTP
        host: 192.168.1.10
        port: 80
        points: 100
        accounts:
          - username: admin
            password: secret
        environments:
          - name: DATABASE_URL
            value: mysql://...
        properties:
          - name: url_path
            value: /index.html
```

**Competition Class:**
- Parses YAML file
- Validates structure and required fields
- Creates database objects (teams, users, services, etc.)
- Handles password hashing
- Validates check names against available checks

## Development Workflows

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/scoringengine/scoringengine.git
cd scoringengine

# Build all services
docker compose build

# Start all services
docker compose up

# OR: Start with example data
SCORINGENGINE_EXAMPLE=true docker compose up

# OR: Reset database and start fresh
SCORINGENGINE_OVERWRITE_DB=true docker compose up

# Access at http://localhost
# Login credentials in README.md
```

**Note**: The project uses `docker compose` (V2 plugin syntax) rather than the deprecated `docker-compose` command.

**Using Makefile:**
```bash
# Build and run
make build
make run

# Run with demo data
make run-demo

# Stop services
make stop

# Clean up (removes volumes)
make clean

# Rebuild from scratch
make rebuild-new
```

### Testing Strategy

**Unit Tests:**
```bash
# Run all unit tests
pytest tests/

# Run with coverage
make run-tests
# OR manually:
coverage run --source=scoring_engine -m pytest -v tests/
coverage report
coverage html

# Run specific test file
pytest tests/scoring_engine/test_competition.py

# Run specific test function
pytest tests/scoring_engine/test_competition.py::test_load_competition

# Run tests matching pattern
pytest -k "test_check"
```

**Integration Tests:**
```bash
# Build integration test environment
make build-integration

# Run integration tests (requires testbed services)
make run-integration-tests
# OR manually:
./tests/integration/run.sh

# Tests run against live services (SSH, HTTP, MySQL, etc.)
```

**Test Structure:**
- `tests/conftest.py`: Pytest configuration with `--integration` flag
- `tests/scoring_engine/helpers.py`: Common test fixtures
- `tests/scoring_engine/unit_test.py`: Base test class with database setup
- Tests mirror production structure: `tests/scoring_engine/models/test_team.py`

**Test Patterns:**
```python
import pytest
from tests.scoring_engine.unit_test import UnitTest

class TestModel(UnitTest):
    def test_something(self):
        # Test has access to self.session (database)
        # Use helpers.py fixtures for common objects
        pass
```

**Important Testing Notes:**
- Unit tests use mock config via `tests/mock_config.py`
- Integration tests require `--integration` flag
- Database is reset for each test class
- All new code MUST have tests (as per user requirement)
- Python 3.14+ required (base image: `python:3.14.2-slim-bookworm`)

### Code Quality & Linting

**Pre-commit Hooks (.pre-commit-config.yaml):**
```bash
# Install pre-commit
pip install pre-commit
pre-commit install

# Run on changed files before commit
pre-commit run --files <changed-files>

# Run on all files
pre-commit run --all-files
```

**Configured Hooks:**
1. **black** (v24.3.0): Code formatter
   - Automatically formats Python code
   - Line length: 120 characters (default)

2. **isort** (v5.13.2): Import sorter
   - Organizes imports alphabetically
   - Groups: stdlib, third-party, local

3. **flake8** (v7.1.1): Linter
   - Configuration in `.flake8`
   - Ignores: E501 (line too long - handled by black)
   - Excludes: `__init__.py`, `.git`

**Manual Linting:**
```bash
# Run black
black scoring_engine/ tests/

# Run isort
isort scoring_engine/ tests/

# Run flake8
flake8 scoring_engine/ tests/
```

**Code Style Guidelines:**
- Follow PEP 8
- Max line length: 120-160 characters
- Use descriptive variable names
- Add docstrings for complex functions
- Type hints encouraged but not required
- Keep functions focused and small

### Version Management

**Using bump-my-version:**
```bash
# Install (included in tests/requirements.txt)
pip install bump-my-version

# Check current version
bump-my-version show current_version
# OR:
python -c "from scoring_engine.version import version; print(version)"

# Bump version (creates commit + tag)
bump-my-version bump patch  # 1.0.0 -> 1.0.1
bump-my-version bump minor  # 1.0.0 -> 1.1.0
bump-my-version bump major  # 1.0.0 -> 2.0.0

# Dry run to preview
bump-my-version bump --dry-run --verbose patch

# Push (triggers CI/CD)
git push origin <branch>
git push --tags
```

**What Gets Updated:**
- `pyproject.toml`: version field
- `setup.py`: version variable
- `scoring_engine/version.py`: version string
- Git commit: "Bump version: X.Y.Z → X.Y.Z+1"
- Git tag: `vX.Y.Z`

**Semantic Versioning:**
- **Patch** (0.0.X): Bug fixes, backward compatible
- **Minor** (0.X.0): New features, backward compatible
- **Major** (X.0.0): Breaking changes, incompatible API changes

### Git Workflow

**Branch Strategy:**
- `master`: Main branch, stable code
- Feature branches: `feature/description` or `claude/description-XXXXX`
- Bug fixes: `fix/description`

**Commit Guidelines:**
- Use descriptive commit messages
- Reference issues where applicable
- Scope commits to logical changes
- Run tests before committing
- Run pre-commit hooks

**CI/CD (GitHub Actions):**

1. **tests.yml**: Runs on all pushes and PRs
   - Installs Python dependencies
   - Runs unit tests (`make run-tests`)
   - Runs integration tests (`./tests/integration/run.sh`)
   - Uploads coverage to Coveralls

2. **publish-images.yml**: Runs on version tags (`v*`) and master pushes
   - Builds multi-architecture Docker images (linux/amd64, linux/arm64)
   - Publishes to GitHub Container Registry (ghcr.io)
   - Publishes to Docker Hub (scoringengine/*)
   - Uses registry cache for faster builds
   - Supports manual trigger with `publish_latest` option
   - Tags: `develop` for master, version tag for releases, `latest` for releases

3. **codeql.yml**: Security analysis
   - Scans for security vulnerabilities
   - Runs on schedule and PR

4. **snyk-container-analysis.yml**: Container security
   - Scans Docker images for vulnerabilities

### Airgapped/Offline Deployments

**CRITICAL**: Many competitions run in completely airgapped environments with NO internet access.

**Quick Method:**
```bash
# On internet-connected system
./bin/create-airgapped-package.sh

# This creates: scoringengine-airgapped.tar.gz
# Transfer to airgapped environment

# On airgapped system
tar -xzf scoringengine-airgapped.tar.gz
cd scoringengine-airgapped
./deploy.sh
```

**Manual Method:**
```bash
# 1. Build all images (with internet)
docker compose build --no-cache

# 2. Export images
mkdir docker-images
docker save python:3.14.2-slim-bookworm -o docker-images/python-base.tar
docker save redis:7.0.4 -o docker-images/redis.tar
docker save mariadb:10 -o docker-images/mariadb.tar
docker save nginx:1.23.1 -o docker-images/nginx.tar
docker save scoringengine/base -o docker-images/scoringengine-base.tar
docker save scoringengine/bootstrap -o docker-images/scoringengine-bootstrap.tar
docker save scoringengine/engine -o docker-images/scoringengine-engine.tar
docker save scoringengine/worker -o docker-images/scoringengine-worker.tar
docker save scoringengine/web -o docker-images/scoringengine-web.tar

# 3. Package and transfer
tar -czf scoringengine-airgapped.tar.gz docker-images/ scoring_engine/ docker/ bin/ configs/ docker-compose.yml engine.conf.inc

# 4. On airgapped system, load images
docker load -i docker-images/python-base.tar
docker load -i docker-images/redis.tar
# ... (load all images)

# 5. Deploy
docker compose up -d
```

**Key Principle**: ALL dependencies must be vendored BEFORE entering airgapped environment. No internet access means:
- No `apt install` or `yum install`
- No `pip install`
- No `docker pull`
- All dependencies embedded in Docker image layers

See `docs/source/installation/airgapped.rst` for complete guide.

**Docker Image Registries:**
Images are published to both registries:
- **GitHub Container Registry**: `ghcr.io/scoringengine/scoringengine/<image>:<tag>`
- **Docker Hub**: `scoringengine/<image>:<tag>`

Available images: `base`, `bootstrap`, `engine`, `web`, `worker`
Tags: `latest`, `develop`, `v1.1.0`, etc.

## Common Development Tasks

### Adding a New Service Check

1. **Create check file**: `scoring_engine/checks/myservice.py`
```python
from scoring_engine.engine.basic_check import BasicCheck

class MyServiceCheck(BasicCheck):
    required_properties = ['username', 'password']
    CMD_TIMEOUT = 30

    def command_format(self, properties):
        return 'myservice-cli --host {host} --user {username} --pass {password}'.format(
            host=self.host,
            username=properties['username'],
            password=properties['password']
        )
```

2. **Add test**: `tests/scoring_engine/checks/test_myservice.py`
```python
from scoring_engine.checks.myservice import MyServiceCheck

def test_myservice_command_format():
    check = MyServiceCheck('192.168.1.1', 1234, {'username': 'admin', 'password': 'secret'})
    command = check.command_format(check.properties)
    assert 'myservice-cli' in command
    assert '192.168.1.1' in command
```

3. **Test the check**:
```bash
pytest tests/scoring_engine/checks/test_myservice.py
```

4. **Document it**: Add `docs/source/checks/myservice.rst`

5. **Add to competition.yaml** for testing:
```yaml
services:
  - name: My Service
    check_name: MyService
    host: 192.168.1.10
    port: 1234
    points: 100
    properties:
      - name: username
        value: admin
      - name: password
        value: secret
```

**Note**: Checks are auto-discovered by scanning `checks/` directory. No registration needed.

### Modifying the Web Interface

**Adding a new route:**
```python
# In scoring_engine/web/views/myview.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user

mod = Blueprint('myview', __name__)

@mod.route('/mypage')
@login_required
def mypage():
    # Access current_user.team, current_user.is_blue_team, etc.
    return render_template('mypage.html', data=...)
```

**Register blueprint in `scoring_engine/web/__init__.py`**

**Create template**: `scoring_engine/web/templates/mypage.html`
```html
{% extends "base.html" %}
{% block content %}
<h1>My Page</h1>
<p>{{ data }}</p>
{% endblock %}
```

**Add API endpoint:**
```python
# In scoring_engine/web/views/api/myapi.py
from flask import jsonify
from flask_login import login_required

@mod.route('/api/mydata')
@login_required
def get_mydata():
    return jsonify({
        'status': 'success',
        'data': [...]
    })
```

### Database Schema Changes

1. **Modify model**: Edit file in `scoring_engine/models/`
```python
# Add new column
new_field = db.Column(db.String(255), nullable=True)
```

2. **Test changes**: Run with `SCORINGENGINE_OVERWRITE_DB=true` to recreate DB

3. **For production**: Generate migration script (manual - no Alembic currently)

4. **Update related code**: Views, templates, competition.py, etc.

### Working with the Cache

**Cache is Redis-based** via Flask-Caching:

```python
from scoring_engine.cache import cache

# Get from cache
value = cache.get('key')

# Set cache
cache.set('key', value, timeout=300)  # 5 minutes

# Delete from cache
cache.delete('key')

# Clear all cache
cache.clear()
```

**Settings Cache:**
```python
from scoring_engine.models.setting import Setting

# Automatically cached
value = Setting.get_setting('setting_name')

# Cache is invalidated when settings change
```

**Scoreboard Cache:**
```python
from scoring_engine.cache_helper import update_all_cache

# Update all cached data (called after each round)
update_all_cache()
```

## Architecture Patterns

### Celery Task Queue Pattern

**Why**: Checks must run in parallel across hundreds of services

**Flow**:
1. Engine creates Round in database
2. For each team's services:
   - Engine queues Celery task: `execute_check.delay(service_id, round_id)`
3. Multiple workers pull tasks from Redis queue
4. Each worker executes check and stores result
5. Engine waits for all tasks to complete
6. Cache updated with new scores

**Celery Configuration**:
- Broker: Redis (`redis://redis:6379/0`)
- Backend: Redis (for result storage)
- Concurrency: Multiple workers, multiple threads each
- Task serialization: JSON

### Database Session Management

**Pattern**: Different contexts use different session strategies

**Engine** (scoring_engine/engine/engine.py):
```python
# Manual session management
from scoring_engine.db import session

# Use session
team = session.query(Team).first()

# Commit changes
session.commit()

# Rollback on error
session.rollback()
```

**Web** (Flask-SQLAlchemy):
```python
# Auto-managed per request
from scoring_engine.models.team import Team

# Session automatically handled
team = Team.query.filter_by(id=1).first()
# Auto-commit at end of request
```

**Tests**:
```python
# Test base class handles session
class TestModel(UnitTest):
    def test_something(self):
        # self.session available
        team = self.session.query(Team).first()
```

### Dynamic Check Loading

**Pattern**: Checks are plugins loaded at runtime

```python
# engine/engine.py
@staticmethod
def load_check_files(checks_location):
    # Scan directory for *.py files
    # Dynamically import each module
    # Find classes inheriting from BasicCheck
    # Return list of check classes

# Example:
checks = Engine.load_check_files('scoring_engine/checks')
# Returns: [SSHCheck, HTTPCheck, DNSCheck, ...]
```

**Benefits**:
- No registration required
- Add check by creating file
- Extensible without core changes

### Role-Based Access Control

**Pattern**: User model has team relationship determining permissions

```python
# In views
from flask_login import current_user

# Check role
if current_user.is_white_team:
    # White team can manage competition
    pass
elif current_user.is_blue_team:
    # Blue team can view their services
    pass
elif current_user.is_red_team:
    # Red team has different access
    pass

# Enforce in templates
{% if current_user.is_white_team %}
<a href="{{ url_for('admin.index') }}">Admin</a>
{% endif %}
```

**Team Types**:
- **White Team**: Competition organizers (full access)
- **Blue Team**: Defenders (view own services, submit flags)
- **Red Team**: Attackers (different scoring, agent checks)

## Security Considerations

**This platform handles sensitive competition data**:

### Authentication & Authorization
- Passwords: bcrypt hashing (bcrypt.hashpw)
- Sessions: Flask-Login with secure cookies
- CSRF: Flask-WTF protection on forms
- Authorization: Team-based access control

### Service Credentials
- Stored in database (accounts table)
- Used for check authentication
- **Never log credentials** in check output
- Sanitize check results before display

### Input Validation
- Validate all user input in views
- Sanitize YAML competition files
- Validate service properties
- Escape output in templates (Jinja2 auto-escapes)

### Docker Security
- Non-root user in containers where possible
- Minimal base images (slim-bookworm)
- Regular security scanning (Snyk, CodeQL)
- Network isolation via Docker networks

**When Modifying Code**:
1. Validate user input (forms, API)
2. Check authorization (team membership, role)
3. Sanitize check outputs (remove sensitive data)
4. Don't log passwords or tokens
5. Use parameterized queries (SQLAlchemy ORM handles this)
6. Escape template output (Jinja2 default)

## Troubleshooting & Debugging

### Common Issues

**1. Database connection errors**
```bash
# Check MySQL is running
docker compose ps mysql

# Check connection from web container
docker compose exec web bash
mysql -h mysql -u scoring_engine -p

# Reset database
SCORINGENGINE_OVERWRITE_DB=true docker compose up
```

**2. Redis connection errors**
```bash
# Check Redis is running
docker compose ps redis

# Test connection
docker compose exec redis redis-cli
> PING
PONG
```

**3. Celery workers not processing tasks**
```bash
# Check worker logs
docker compose logs -f worker

# Check Redis queue
docker compose exec redis redis-cli
> KEYS *
> LLEN celery

# Restart workers
docker compose restart worker
```

**4. Check timeouts**
```bash
# Increase timeout in check class
class MyCheck(BasicCheck):
    CMD_TIMEOUT = 60  # Increase from default 30

# Or in execute_command.py modify DEFAULT_TIMEOUT
```

**5. Import errors**
```bash
# Ensure package installed in development mode
pip install -e .

# Check PYTHONPATH
export PYTHONPATH=/path/to/scoringengine:$PYTHONPATH
```

### Debugging Tools

**View logs:**
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f web
docker compose logs -f engine
docker compose logs -f worker

# Follow new logs
docker compose logs -f --tail=100 web
```

**Access containers:**
```bash
# Web container
docker compose exec web bash

# Engine container
docker compose exec engine bash

# Database
docker compose exec mysql mysql -u scoring_engine -p scoringengine
```

**Database queries:**
```bash
# Access MySQL
docker compose exec mysql mysql -u scoring_engine -p

# Useful queries
SHOW TABLES;
SELECT * FROM team;
SELECT * FROM service;
SELECT * FROM check ORDER BY id DESC LIMIT 10;
SELECT COUNT(*) FROM check WHERE result='Correct';
```

**Redis debugging:**
```bash
# Access Redis CLI
docker compose exec redis redis-cli

# Check keys
KEYS *

# Check queue length
LLEN celery

# Monitor commands
MONITOR

# Check cached values
GET scoreboard_json
```

**Python debugging:**
```python
# Add to code
import pdb; pdb.set_trace()

# Or use print debugging
print(f"DEBUG: variable={variable}")

# Or use logging
from scoring_engine.logger import logger
logger.debug("Debug message")
logger.info("Info message")
logger.error("Error message")
```

## File Location Quick Reference

| Task | File Location |
|------|---------------|
| Add service check | `scoring_engine/checks/mycheck.py` |
| Modify database model | `scoring_engine/models/` |
| Change web UI | `scoring_engine/web/views/` + `templates/` |
| Add API endpoint | `scoring_engine/web/views/api/` |
| Fix check execution | `scoring_engine/engine/` |
| Adjust configuration | `config_loader.py`, `engine.conf.inc` |
| Add Python dependency | `pyproject.toml` dependencies list |
| Modify Docker setup | `docker/` + `docker-compose.yml` |
| Update tests | `tests/scoring_engine/` (mirrors structure) |
| Add documentation | `docs/source/` |
| Change version | `bump-my-version bump [patch\|minor\|major]` |
| Modify CI/CD | `.github/workflows/` |

## Important Files to Know

### Configuration Files
- **pyproject.toml**: Python package metadata and dependencies
- **setup.py**: Legacy setup script (being phased out)
- **engine.conf.inc**: Default configuration template
- **.flake8**: Linter configuration (ignores E501)
- **.pre-commit-config.yaml**: Pre-commit hook setup
- **.bumpversion.cfg**: Version bump configuration
- **docker-compose.yml**: Service orchestration

### Entry Points
- **bin/setup**: Initial database setup
- **bin/engine**: Engine entry point
- **bin/web**: Web UI entry point
- **bin/worker**: Celery worker entry point
- **bin/competition.yaml**: Example competition definition

### Core Application Files
- **scoring_engine/db.py**: Database session setup
- **scoring_engine/config.py**: Configuration object
- **scoring_engine/config_loader.py**: Config loading logic
- **scoring_engine/celery_app.py**: Celery configuration
- **scoring_engine/cache.py**: Flask-Caching setup
- **scoring_engine/cache_helper.py**: Cache update utilities
- **scoring_engine/competition.py**: YAML parsing and loading
- **scoring_engine/version.py**: Version string

### Documentation
- **README.md**: Quick start guide
- **VERSION_MANAGEMENT.md**: Version bumping workflow
- **AGENTS.md**: Basic agent guidelines
- **docs/source/**: Full Sphinx documentation

## Best Practices for AI Assistants

### When Exploring the Codebase

1. **Start with models**: Understanding data structure helps navigate everything else
2. **Follow the flow**: Web route → View logic → Model → Database
3. **Check tests**: Tests show usage examples and expected behavior
4. **Read existing patterns**: New code should match existing style
5. **Check documentation**: `docs/source/` has detailed guides

### When Making Changes

1. **Always read files first**: Never propose changes to code you haven't read
2. **Match existing patterns**: Look at similar code for style guidance
3. **Write tests**: All new code must have tests (user requirement)
4. **Run linters**: Use pre-commit hooks before committing
5. **Avoid over-engineering**: Make minimal changes to accomplish the goal
6. **Don't add unnecessary features**: No unsolicited refactoring or improvements
7. **Security first**: Validate input, check authorization, sanitize output
8. **Test locally**: Use docker compose to verify changes work

### When Adding New Features

1. **Understand the pattern**: Check how similar features are implemented
2. **Follow the structure**: Place files in appropriate directories
3. **Update documentation**: Add RST files in docs/source/
4. **Add tests**: Unit tests + integration tests where applicable
5. **Update competition.yaml**: If adding check, include example config
6. **Consider airgapped**: Ensure new dependencies are vendorable

### When Fixing Bugs

1. **Reproduce first**: Understand the issue before fixing
2. **Add regression test**: Prevent bug from reoccurring
3. **Minimal fix**: Don't refactor surrounding code unnecessarily
4. **Test thoroughly**: Verify fix works and doesn't break other things
5. **Check related code**: Similar bugs might exist elsewhere

### Code Style Preferences

- **Imports**: Use isort, group by stdlib/third-party/local
- **Formatting**: Use black (line length 120)
- **Naming**: Descriptive names, snake_case for functions/variables
- **Docstrings**: Add for complex functions, not required for simple ones
- **Comments**: Only where logic isn't self-evident
- **Type hints**: Encouraged but not required
- **Error handling**: Catch specific exceptions, log errors
- **Database queries**: Use SQLAlchemy ORM, avoid raw SQL

### Things to Avoid

- ❌ Creating documentation files without being asked
- ❌ Adding features not requested
- ❌ Refactoring code unnecessarily
- ❌ Adding backwards-compatibility hacks
- ❌ Creating abstractions for one-time use
- ❌ Adding error handling for impossible scenarios
- ❌ Over-commenting obvious code
- ❌ Changing code style in files you're not modifying
- ❌ Committing without running tests
- ❌ Pushing to master without PR

## Additional Resources

### Documentation
- **Full Docs**: https://scoringengine.readthedocs.io/
- **Local Docs**: `make -C docs html` → `docs/build/html/index.html`
- **API Reference**: Check docstrings in code

### External Dependencies
- **Flask**: https://flask.palletsprojects.com/
- **SQLAlchemy**: https://www.sqlalchemy.org/
- **Celery**: https://docs.celeryproject.org/
- **Redis**: https://redis.io/documentation
- **Docker**: https://docs.docker.com/

### Community
- **GitHub Issues**: https://github.com/scoringengine/scoringengine/issues
- **GitHub Discussions**: For questions and discussions

---

## Summary for Quick Reference

**This is a Flask + Celery + SQLAlchemy application for cybersecurity competitions.**

**Architecture**: Web UI (Flask) + Engine (scheduler) + Workers (Celery) + Database (MySQL) + Cache (Redis)

**Key Directories**:
- `scoring_engine/checks/`: Service check implementations
- `scoring_engine/models/`: Database models
- `scoring_engine/engine/`: Competition orchestration
- `scoring_engine/web/`: Flask application
- `tests/`: Mirror structure of main code

**Development**:
- Run: `docker compose up` (or `make run`)
- Test: `pytest tests/` (or `make run-tests`)
- Lint: `pre-commit run --all-files`
- Version: `bump-my-version bump [patch|minor|major]`

**Testing Required**: All new code MUST have tests

**Common Tasks**:
- Add check: Create file in `checks/`, add test
- Modify UI: Edit `web/views/` and `templates/`
- Change schema: Edit `models/`, test with fresh DB
- Add API: Add to `web/views/api/`

**Security**: Validate input, check authorization, sanitize output, don't log credentials

**Airgapped**: Use `./bin/create-airgapped-package.sh` for offline deployments

**When in doubt**: Check existing patterns, read tests, follow the architecture
