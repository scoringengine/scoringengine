Base Setup
----------
.. note:: These instructions are for Ubuntu 22.04 or newer. Docker is the recommended deployment method.

Requirements
^^^^^^^^^^^^
- **Python 3.10 or higher**
- MariaDB/MySQL database server
- Redis server

Install dependencies via apt-get
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  apt-get update
  apt-get install -y python3 python3-pip python3-venv wget git build-essential libmariadb-dev

Create engine user
^^^^^^^^^^^^^^^^^^
::

  useradd -m engine

Setup virtual environment
^^^^^^^^^^^^^^^^^^^^^^^^^
::

  su engine
  cd ~/
  mkdir /home/engine/scoring_engine
  python3 -m venv /home/engine/scoring_engine/env

Setup src directory
^^^^^^^^^^^^^^^^^^^
::

  git clone https://github.com/scoringengine/scoringengine /home/engine/scoring_engine/src

Install scoring_engine src python dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  source /home/engine/scoring_engine/env/bin/activate
  pip install -e /home/engine/scoring_engine/src/

Copy/Modify configuration
^^^^^^^^^^^^^^^^^^^^^^^^^
::

  cp /home/engine/scoring_engine/src/engine.conf.inc /home/engine/scoring_engine/src/engine.conf
  vi /home/engine/scoring_engine/src/engine.conf

Create log file locations (run as root)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  mkdir /var/log/scoring_engine
  chown -R syslog:adm /var/log/scoring_engine

Copy rsyslog configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  cp /home/engine/scoring_engine/src/configs/rsyslog.conf /etc/rsyslog.d/10-scoring_engine.conf

Restart rsyslog
^^^^^^^^^^^^^^^
::

  systemctl restart rsyslog
