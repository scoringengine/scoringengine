Development
***********

.. note:: Currently we support python 3 with `virtual environments <http://docs.python-guide.org/en/latest/dev/virtualenvs/#lower-level-virtualenv>`_

Setup Configuration
-------------------
::

  cp engine.conf.inc engine.conf
  sed -i '' 's/debug = False/debug = True/g' engine.conf

.. note:: If the debug config value is set to True, the web ui will automatically reload on changes to files, and will tell the web ui to listen only on localhost with port 5000

Install Development Dependencies
--------------------------------
::

  pip install -r tests/requirements.txt


Populate Sample DB
------------------
::

  python bin/populate_db --example --overwrite-db

Run Services
------------
Web UI
^^^^^^
::

  python bin/web

Then, access `localhost:5000 <http:localhost:5000>`_

Credentials:

* whiteteamuser:testpass
* team1user1:testpass
* team2user1:testpass
* team2user2:testpass
* redteamuser:testpass

.. note:: The engine and worker do NOT need to be running in order to run the web UI.

Engine
^^^^^^
::

  python bin/engine

Worker
^^^^^^
::

  python bin/worker

Run Tests
---------
We use the `pytest <https://docs.pytest.org/en/latest/>`_ testing framework.

.. note:: The tests use a separate db (sqlite in memory), so don't worry about corrupting a production db when running the tests.

::

  py.test tests

.. hint:: Instead of specifying the tests directory, you can specify specific file(s) to run: *pytest tests/scoring_engine/test_config.py*
