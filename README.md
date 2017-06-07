[![Build Status](https://travis-ci.org/pwnbus/scoring_engine.svg?branch=master)](https://travis-ci.org/pwnbus/scoring_engine)
[![Code Climate](https://codeclimate.com/github/pwnbus/scoring_engine/badges/gpa.svg)](https://codeclimate.com/github/pwnbus/scoring_engine)
[![Test Coverage](https://codeclimate.com/github/pwnbus/scoring_engine/badges/coverage.svg)](https://codeclimate.com/github/pwnbus/scoring_engine/coverage)
# scoring_engine
Scoring Engine for Red/White/Blue Team Competitions

# DEV INSTRUCTIONS

1. Install Vagrant

2. Install Virtualbox

3. Fork this repo

4. Clone your fork

5. `vagrant up` then `vagrant ssh`

6. `cd /vagrant; pip install -e .`

7. `systemctl start redis-server`

8. `py.test tests`

# Docker INSTRUCTIONS

1. docker build -t scoring_engine:latest .
2. docker run --name scoring_engine -p 5000:5000 -d scoring_engine:latest
