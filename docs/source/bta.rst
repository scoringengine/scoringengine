Black Team Agent (BTA)
**********************

The scoring engine exposes an HTTP API for Black Team Agents (BTAs) to
retrieve flags to plant on hosts and to report flags that have been
planted. Although operated by the Black Team, BTAs run on Blue Team
infrastructure. Their check-ins allow the engine to score agent
availability and verify indicators of compromise via Red Team flags.
BTAs periodically "check in" with the engine.

Configuration
=============

Two settings must be configured before BTAs can communicate with the
engine:

``agent_psk``
  Pre-shared key used to derive per-team encryption keys.

``agent_show_flag_early_mins``
  Number of minutes before a flag becomes active that the agent may
  retrieve flag details.

Check-in
========

A BTA performs a POST request to ``/api/agent/checkin`` with the team
name provided in the ``t`` query parameter. The request body must be an
AES-GCM encrypted JSON document with the following structure::

    {
      "team": "<team name>",
      "host": "<hostname or ip>",
      "plat": "win" | "nix",
      "flags": ["<flag id>", ...]
    }

The AES-GCM key is the SHA-256 hash of ``team_name + agent_psk``. A
random 12 byte nonce is prepended to the encrypted payload. The request
should be sent with the ``Content-Type`` header set to
``application/octet-stream``.

The optional ``flags`` list contains the IDs of any flags that have been
successfully planted since the last check-in.

Response
========

The engine responds with an encrypted payload of the same format. After
decryption the payload resembles::

    {
      "flags": [ { ...flag definition... } ],
      "config": { "checkin_interval": { "secs": <seconds>, "nanos": 0 } },
      "timestamp": <unix timestamp>
    }

``flags`` is the list of new flags to plant. Each flag entry includes
fields such as ``id``, ``type``, ``data``, ``platform``, ``start_time``
and ``end_time``. The agent should report the ``id`` of each flag it
plants in the next check-in.

``config.checkin_interval.secs`` tells the agent how long to wait before
contacting the engine again. This value is taken from the
``agent_checkin_interval_sec`` setting. ``timestamp`` is the server's
current time in seconds since the Unix epoch.

