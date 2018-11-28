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
The engine is responsible for tasking the checks for teams during each round, and determining/saving their results to the database. This process runs for the entirety of the competition, and will sleep for a certain amount of time before starting on to the next round.

Worker
^^^^^^
The worker connects to Redis and waits for checks to get tasked. Once it receives the check, it executes the command and returns the output back to Redis.

Web
^^^
The web application provides a graphical view of the Competition. This includes things like a bar graph of all team's scores as well as a table of the current round results.  This can also be used to configure the properties of services.

External Resources
^^^^^^^^^^^^^^^^^^
We currently use `MySQL <https://www.mysql.com/products/community/>`_ as the database, and `Redis <https://redis.io/>`_ as the data store for tasks while they are getting scheduled.