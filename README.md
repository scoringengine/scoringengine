[![Documentation Status](https://readthedocs.org/projects/scoringengine/badge/?version=latest)](https://scoringengine.readthedocs.io/en/latest/)
[![CI](https://github.com/scoringengine/scoringengine/actions/workflows/tests.yml/badge.svg)](https://github.com/scoringengine/scoringengine/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/scoringengine/scoringengine/badge.svg?branch=master)](https://coveralls.io/github/scoringengine/scoringengine?branch=master)

# Scoring Engine

Scoring Engine is an open-source platform for running Red/White/Blue team cybersecurity competitions. It automates service checks each round and provides a web-based scoreboard and configuration interface.

![Scoring Engine screenshot](https://github.com/scoringengine/scoringengine/blob/master/docs/source/images/screenshots.gif)

## Features

- Automated scheduling and execution of service checks
- Distributed parallel execution via Celery workers and Redis
- Web interface for viewing scores and configuring services
- JSON API for programmatic access to scores and configuration
- 28 built-in service checks (SSH, HTTP, DNS, SMTP, and more)
- Support for airgapped/offline deployments
- Example mode with pre-populated demo data

## Architecture

Scoring Engine uses a distributed architecture with the following components:

| Component | Technology | Purpose |
|-----------|------------|---------|
| Web UI | Flask | Scoreboard, team management, administration |
| Task Queue | Celery | Distributed job scheduling and execution |
| Message Broker | Redis | Task queue backend and caching |
| Database | MySQL/MariaDB | Persistent storage for teams, services, and results |
| Reverse Proxy | Nginx | HTTP server and load balancing |

## Supported Service Checks

Scoring Engine includes checks for common services out of the box:

| Category | Services |
|----------|----------|
| Network | ICMP, DNS, NFS |
| Web | HTTP, HTTPS, Elasticsearch, WordPress |
| Authentication | SSH, Telnet, LDAP, WinRM |
| File Transfer | FTP, SMB |
| Email | SMTP, SMTPS, IMAP, IMAPS, POP3, POP3S |
| Database | MySQL, PostgreSQL, MSSQL |
| Remote Desktop | RDP, VNC |
| VPN | OpenVPN |

Custom checks can be added by creating a Python class in `scoring_engine/checks/`.

## Prerequisites

### Docker Installation (Recommended)

- [Docker](https://www.docker.com/products/overview)
- [Docker Compose](https://docs.docker.com/compose/) (included with Docker Desktop; on Linux install separately)
- For Windows users, ensure Docker Desktop is set to [use Linux containers](https://docs.docker.com/docker-for-windows/#switch-between-windows-and-linux-containers).

### Source Installation

For installing from source without Docker:

- **Python 3.10 or higher** is required
- MariaDB/MySQL database server
- Redis server

```bash
# Install the package
pip install -e .

# Or install with test dependencies
pip install -e .
pip install -r tests/requirements.txt
```

## Quick Start

Build and start all services:

```bash
docker compose build
docker compose up
```

Or use the Makefile for convenience:

```bash
make build
make run
```

Once running, access the application at [http://localhost](http://localhost/).

### Demo Credentials

Log in using any of the following credentials:

| Username | Password | Role |
|----------|----------|------|
| `whiteteamuser` | `testpass` | White Team (Admin) |
| `team1user1` | `testpass` | Blue Team 1 |
| `team2user1` | `testpass` | Blue Team 2 |
| `team2user2` | `testpass` | Blue Team 2 |
| `redteamuser` | `testpass` | Red Team |

### Environment Variables

Reset the database before starting:

```bash
SCORINGENGINE_OVERWRITE_DB=true docker compose up
```

Run with sample data (demo mode):

```bash
SCORINGENGINE_EXAMPLE=true docker compose up
```

Or combine both for a fresh demo:

```bash
make run-demo
```

## Pre-built Docker Images

Pre-built images are available from both registries:

- **GitHub Container Registry**: `ghcr.io/scoringengine/scoringengine/<image>:<tag>`
- **Docker Hub**: `scoringengine/<image>:<tag>`

Available images: `base`, `bootstrap`, `engine`, `web`, `worker`

Tags: `latest`, `develop`, version tags (e.g., `v1.1.0`)

## Airgapped Deployments

For competitions with no internet access:

```bash
# Create a complete deployment package
./bin/create-airgapped-package.sh

# Transfer scoringengine-airgapped.tar.gz to the airgapped system
# Then extract and deploy:
tar -xzf scoringengine-airgapped.tar.gz
cd scoringengine-airgapped
./deploy.sh
```

See the [Airgapped Deployment Guide](docs/source/installation/airgapped.rst) for detailed instructions.

## Development

### Makefile Commands

| Command | Description |
|---------|-------------|
| `make build` | Build all Docker images |
| `make run` | Start all services |
| `make run-demo` | Start with demo data (resets database) |
| `make stop` | Stop all services |
| `make clean` | Stop services and remove volumes |
| `make rebuild-new` | Full rebuild with fresh database |
| `make run-tests` | Run unit tests with coverage |
| `make build-integration` | Build integration test environment |
| `make run-integration-tests` | Run integration tests |

### Running Tests

Run the linters and test suite before submitting changes:

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Run linters on changed files
pre-commit run --files <changed-files>

# Run all tests
pytest tests/

# Run tests with coverage
make run-tests
```

To check all files: `pre-commit run --all-files`

### Building Documentation Locally

```bash
pip install -r docs/requirements.txt
cd docs
make html
```

Open `docs/build/html/index.html` in your browser.

## Version Management

This project uses semantic versioning. To bump versions:

```bash
# Install development dependencies
pip install -r tests/requirements.txt

# Bump version (patch/minor/major)
bump-my-version bump patch
```

See [VERSION_MANAGEMENT.md](VERSION_MANAGEMENT.md) for detailed instructions.

## Documentation

Full documentation is available at [https://scoringengine.readthedocs.io/en/latest/](https://scoringengine.readthedocs.io/en/latest/).

## License

Released under the [MIT License](LICENSE).
