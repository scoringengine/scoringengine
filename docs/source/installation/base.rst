Base Setup
----------
.. note:: Currently, the only OS we have documentation on is Ubuntu 16.04.

Install dependencies via apt-get
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  apt-get update
  apt-get install -y python3.5 wget git python3.5-dev build-essential libmysqlclient-dev

Create engine user
^^^^^^^^^^^^^^^^^^
::

  useradd -m engine

Download and Install pip
^^^^^^^^^^^^^^^^^^^^^^^^
::

  wget -O /root/get-pip.py https://bootstrap.pypa.io/get-pip.py
  python3.5 /root/get-pip.py
  rm /root/get-pip.py

Setup virtualenvironment
^^^^^^^^^^^^^^^^^^^^^^^^
::

  pip install virtualenv
  su engine
  cd ~/
  mkdir /home/engine/scoring_engine
  virtualenv -p /usr/bin/python3.5 /home/engine/scoring_engine/env

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
