*************
API
*************

The Scoring Engine exposes a JSON-based API used by the web interface and
automation. These endpoints allow programmatic access to scoring data and
engine management.

Scoreboard
==========

* ``/api/scoreboard/get_bar_data`` – aggregate team scores.
* ``/api/scoreboard/get_line_data`` – per-round scoring trends.

Teams and Services
==================

* ``/api/team/<team_id>/stats`` – statistics for a team's services.
* ``/api/service/<service_id>/checks`` – check history for a service.

Administration
==============

Administrative endpoints support managing competition settings, such as
updating service properties and toggling the engine. These APIs are
secured and intended for white team use.

Flags and Injects
=================

Endpoints under ``/api/flags`` and ``/api/admin/injects`` support
capture-the-flag style challenges and graded injects.

Example
=======

Retrieve scoreboard data as JSON:

.. code-block:: bash

   curl http://localhost/api/scoreboard/get_bar_data
