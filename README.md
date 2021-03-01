[![Documentation Status](https://readthedocs.org/projects/scoringengine/badge/?version=latest)](https://scoringengine.readthedocs.io/en/latest/)
[![CI](https://github.com/scoringengine/scoringengine/actions/workflows/tests.yml/badge.svg)](https://github.com/scoringengine/scoringengine/actions/workflows/tests.yml)
[![Test Coverage](https://api.codeclimate.com/v1/badges/3086b9e946c109140ac3/test_coverage)](https://codeclimate.com/github/scoringengine/scoringengine/test_coverage)

Scoring Engine
==============
Scoring Engine for Red/White/Blue Team Competitions

<img src="https://github.com/scoringengine/scoringengine/blob/master/docs/source/images/screenshots.gif" width="800" height="577" />

Getting started
---------------

Download [Docker](https://www.docker.com/products/overview). If you are on Mac or Windows, [Docker Compose](https://docs.docker.com/compose) will be automatically installed. On Linux, make sure you have the latest version of [Compose](https://docs.docker.com/compose/install/). If you're using [Docker for Windows](https://docs.docker.com/docker-for-windows/) on Windows 10 pro or later, you must also [switch to Linux containers](https://docs.docker.com/docker-for-windows/#switch-between-windows-and-linux-containers).

Run in this directory:
```
docker-compose build
docker-compose up
```

If you want to delete the database before starting, set the SCORINGENGINE_OVERWRITE_DB environment variable:
```
SCORINGENGINE_OVERWRITE_DB=true docker-compose up
```

We also provide the ability to run it in an 'example' mode. This means only the web ui runs, and the database is prepopulated with example data. Set the SCORINGENGINE_EXAMPLE environment variable to true:
```
SCORINGENGINE_EXAMPLE=true docker-compose up
```

The app will be running at [http://localhost](http://localhost)

Log in with any of the following logins at http://localhost:
* whiteteamuser:testpass
* team1user1:testpass
* team2user1:testpass
* team2user2:testpass
* redteamuser:testpass

Documentation
-------------
[https://scoringengine.readthedocs.io/en/latest/](https://scoringengine.readthedocs.io/en/latest/)
