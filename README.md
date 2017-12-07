[![Build Status](https://travis-ci.org/pwnbus/scoring_engine.svg?branch=master)](https://travis-ci.org/pwnbus/scoring_engine)
[![Maintainability](https://api.codeclimate.com/v1/badges/b75e38be913b45250ed2/maintainability)](https://codeclimate.com/github/pwnbus/scoring_engine/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/b75e38be913b45250ed2/test_coverage)](https://codeclimate.com/github/pwnbus/scoring_engine/test_coverage)
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
2. docker run --name scoring_engine -p 127.0.0.1:5000:5000 -d scoring_engine:latest
3. Login with any of the following logins at http://127.0.0.1:5000:
    - whiteteamuser:testpass
    - team1user1:testpass
    - team2user1:testpass
    - team2user2:testpass
    - redteamuser:testpass
 