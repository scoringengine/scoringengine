[![Documentation Status](https://readthedocs.org/projects/scoringengine/badge/?version=latest)](https://scoringengine.readthedocs.io/en/latest/)
[![CI](https://github.com/scoringengine/scoringengine/actions/workflows/tests.yml/badge.svg)](https://github.com/scoringengine/scoringengine/actions/workflows/tests.yml)
[![Coverage Status](https://coveralls.io/repos/github/scoringengine/scoringengine/badge.svg?branch=master)](https://coveralls.io/github/scoringengine/scoringengine?branch=master)

# Scoring Engine

Scoring Engine is an open-source platform for running Red/White/Blue team competitions. It automates service checks each round and provides a web-based scoreboard and configuration interface.

![Scoring Engine screenshot](https://github.com/scoringengine/scoringengine/blob/master/docs/source/images/screenshots.gif)

## Features

- Automated scheduling and execution of service checks
- Redis-backed workers for parallel execution
- Web interface for viewing scores and configuring services
- JSON API for programmatic access to scores and configuration
- Example mode with pre-populated demo data

## Prerequisites

- [Docker](https://www.docker.com/products/overview)
- [Docker Compose](https://docs.docker.com/compose/) (included with Docker Desktop; on Linux install separately)
- For Windows users, ensure Docker Desktop is set to [use Linux containers](https://docs.docker.com/docker-for-windows/#switch-between-windows-and-linux-containers).

## Quick Start

From this directory run:

```bash
docker-compose build
docker-compose up
```

### Optional environment variables

Reset the database before starting:

```bash
SCORINGENGINE_OVERWRITE_DB=true docker-compose up
```

Run with sample data and only the web UI:

```bash
SCORINGENGINE_EXAMPLE=true docker-compose up
```

Once running, access the application at [http://localhost](http://localhost/).

Log in using any of the following credentials:

- `whiteteamuser:testpass`
- `team1user1:testpass`
- `team2user1:testpass`
- `team2user2:testpass`
- `redteamuser:testpass`

## Documentation

Full documentation is available at [https://scoringengine.readthedocs.io/en/latest/](https://scoringengine.readthedocs.io/en/latest/).

## Building Documentation Locally

To build the documentation locally:

```bash
pip install -r docs/requirements.txt
cd docs
make html
```

Open `docs/build/html/index.html` in your browser to view the rendered documentation.

## Tests and Code Style

Run the linters and test suite before submitting changes:

```bash
pre-commit run --files <changed-files>
pytest
```

To check every file, use `pre-commit run --all-files`.

## License

Released under the [MIT License](LICENSE).

