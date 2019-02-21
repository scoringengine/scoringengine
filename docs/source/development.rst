Development
***********

.. note:: Currently we support 2 ways of working on the Scoring Engine. You can either use the existing `Docker environment <installation/docker.html>`_, or you can run each service locally using python 3. If you choose to do your development locally, we recommend using `virtual environments. <http://docs.python-guide.org/en/latest/dev/virtualenvs/#lower-level-virtualenv>`_


Initial Setup
-------------
These steps are for if you want to do your development locally and run each service locally as well.

Create Config File
^^^^^^^^^^^^^^^^^^
::

  cp engine.conf.inc engine.conf
  sed -i '' 's/debug = False/debug = True/g' engine.conf

.. hint:: If debug is set to True, the web ui will automatically reload on changes to local file modifications, which can help speed up development. This config setting will also tell the worker to output all check output to stdout.

Install Required Dependencies
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
::

  pip install -e .

Populate Sample DB
^^^^^^^^^^^^^^^^^^
::

  python bin/setup --example --overwrite-db


Run Services
------------
Web UI
^^^^^^
::

  python bin/web

Then, access `localhost:5000 <http:localhost:5000>`_

.. list-table:: Credentials
   :header-rows: 1

   * - Username
     - Password
   * - whiteteamuser
     - testpass
   * - redteamuser
     - testpass
   * - team1user1
     - testpass
   * - team2user1
     - testpass
   * - team2user2
     - testpass

.. note:: The engine and worker do NOT need to be running in order to run the web UI.

Engine
^^^^^^
Both the engine and worker services require a redis server to be running. Redis can be easily setup by using the existing docker environment.
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

First, we need to install the dependencies required for testing.
::

  pip install -r tests/requirements.txt

Next, we run our tests
::

  pytest tests

.. hint:: Instead of specifying the tests directory, you can specify specific file(s) to run: *pytest tests/scoring_engine/test_config.py*

Modifying Documentation
-----------------------
We use `sphinx <http://www.sphinx-doc.org/en/master/>`_ to build the documentation.

First, we need to install the dependencies required for documentation.
::

  pip install -r docs/requirements.txt

Next, we build our documentation in html format.
::

  cd docs
  make html
  open build/html/index.html
