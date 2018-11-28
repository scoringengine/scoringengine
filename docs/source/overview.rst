********
Overview
********

Why?
====

The goal of the ScoringEngine is to keep track of service up time in a blue teams/red team competition.

How does it work?
=================

The general idea of the ScoringEngine is broken up into 3 separate processes, Engine, Worker, and Web.

Engine
^^^^^^
The engine is responsible for tasking `Checks` that are used to verify network services each round, and determining/saving their results to the database. This process runs for the entire competition, and will sleep for a certain amount of time before starting on to the next round.

Worker
^^^^^^
The worker connects to Redis and waits for `Checks` to get tasked in order to run them against . Once it receives a
`Check`, it executes the command and sends the output back to the Engine.

Web
^^^
The web application provides a graphical view of the Competition. This includes things like a bar graph of all team's scores as well as a table of the current round's results.  This can also be used to configure the properties of each service per team.

External Resources
^^^^^^^^^^^^^^^^^^
We currently use `MySQL <https://www.mysql.com/products/community/>`_ as the database, and `Redis <https://redis.io/>`_ as the data store for tasks while they are getting scheduled.

Putting it all together
^^^^^^^^^^^^^^^^^^^^^^^
  - The `Engine` starts
  - The first `Round` starts
  - The `Engine` tasks `Checks` out to the `Workers`
  - The `Workers` execute the `Checks` and return the output to the `Engine`
  - The `Engine` waits for all `Checks` to finish
  - The `Engine` determines the results of each `Check`, and saves the results to the DB
  - The `Engine` ends the `Round`
  - The `Engine` sleeps for some time
  - The second `Round` starts
  - ...

.. include:: screenshots.rst