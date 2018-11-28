Engine
------

Install Redis
^^^^^^^^^^^^^
::

  apt-get install -y redis-server

Setup Redis to listen on external interface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  sed -i -e 's/bind 127.0.0.1/bind 0.0.0.0/g' /etc/redis/redis.conf
  systemctl restart redis

Setup Engine service (run as root)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  cp /home/engine/scoring_engine/src/configs/engine.service /etc/systemd/system/scoring_engine-engine.service

Modify configuration
^^^^^^^^^^^^^^^^^^^^
::

  su engine
  vi /home/engine/scoring_engine/src/engine.conf

Setup scoring engine teams and services
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  su engine
  vi /home/engine/scoring_engine/src/bin/competition.yaml
  source /home/engine/scoring_engine/env/bin/activate
  /home/engine/scoring_engine/src/bin/setup

Start engine service (must run as root)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  systemctl start scoring_engine-engine

Monitor engine
^^^^^^^^^^^^^^
::

  journalctl -f _SYSTEMD_UNIT=scoring_engine-engine.service
  tail -f /var/log/scoring_engine/engine.log
