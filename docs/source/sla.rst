SLA Penalties & Dynamic Scoring
*******************************

The scoring engine supports advanced scoring features including SLA (Service Level Agreement) penalties for service downtime and dynamic scoring multipliers based on competition phase.

SLA Penalties
=============

SLA penalties penalize teams when their services experience consecutive failures. This encourages teams to maintain service uptime and quickly recover from outages.

How It Works
------------

1. The system tracks consecutive failed checks for each service
2. Once failures exceed the configured threshold (default: 5), penalties begin
3. Penalties are calculated as a percentage of the service's earned score
4. Different penalty modes determine how penalties accumulate

Configuration
-------------

SLA penalties can be configured via ``engine.conf.inc`` or environment variables:

.. code-block:: ini

   # Enable/disable SLA penalties
   sla_enabled = False

   # Number of consecutive failures before penalties begin
   sla_penalty_threshold = 5

   # Penalty percentage per failure after threshold
   sla_penalty_percent = 10

   # Maximum total penalty percentage
   sla_penalty_max_percent = 50

   # Penalty calculation mode
   sla_penalty_mode = additive

   # Allow scores to go negative
   sla_allow_negative = False

Penalty Modes
-------------

**Additive Mode** (``additive``)
   Penalty accumulates linearly. With threshold=5 and percent=10:

   - 5 failures: 10% penalty
   - 6 failures: 20% penalty
   - 7 failures: 30% penalty
   - etc. (capped at max_percent)

**Flat Mode** (``flat``)
   Fixed penalty per failure after threshold:

   - 5 failures: 0% penalty (at threshold)
   - 6 failures: 10% penalty
   - 7 failures: 20% penalty
   - etc.

**Exponential Mode** (``exponential``)
   Penalty doubles each failure:

   - 5 failures: 10% penalty
   - 6 failures: 20% penalty
   - 7 failures: 40% penalty
   - 8 failures: 80% penalty
   - etc.

**Next Check Reduction** (``next_check_reduction``)
   Similar to additive, but conceptually reduces the value of the next successful check rather than deducting from total score.

Admin Interface
---------------

White team members can configure SLA settings through the web interface at ``/admin/sla``. This page allows:

- Toggling SLA penalties on/off
- Adjusting threshold and penalty values
- Changing penalty mode
- Viewing current SLA status for all teams

API Endpoints
-------------

The following API endpoints provide SLA information:

- ``GET /api/sla/summary`` - SLA summary for all teams
- ``GET /api/sla/team/<team_id>`` - Detailed SLA info for a specific team
- ``GET /api/sla/config`` - Current SLA configuration (admin only)


Dynamic Scoring
===============

Dynamic scoring allows point values to vary based on competition phase. This can be used to:

- Reward early uptime with bonus points
- Reduce point values later in the competition
- Create strategic timing considerations for teams

How It Works
------------

The competition is divided into three phases:

1. **Early Phase** (Rounds 1-N): Points multiplied by early multiplier (e.g., 2x)
2. **Normal Phase** (Rounds N+1 to M-1): Standard 1x multiplier
3. **Late Phase** (Rounds M+): Points multiplied by late multiplier (e.g., 0.5x)

Configuration
-------------

.. code-block:: ini

   # Enable/disable dynamic scoring
   dynamic_scoring_enabled = False

   # Early phase configuration
   dynamic_scoring_early_rounds = 10
   dynamic_scoring_early_multiplier = 2.0

   # Late phase configuration
   dynamic_scoring_late_start_round = 50
   dynamic_scoring_late_multiplier = 0.5

Example Scenarios
-----------------

**Scenario 1: Incentivize Early Uptime**

.. code-block:: ini

   dynamic_scoring_enabled = True
   dynamic_scoring_early_rounds = 20
   dynamic_scoring_early_multiplier = 2.0
   dynamic_scoring_late_start_round = 100
   dynamic_scoring_late_multiplier = 1.0

Teams earn double points for the first 20 rounds, encouraging quick setup.

**Scenario 2: Declining Value**

.. code-block:: ini

   dynamic_scoring_enabled = True
   dynamic_scoring_early_rounds = 10
   dynamic_scoring_early_multiplier = 1.5
   dynamic_scoring_late_start_round = 30
   dynamic_scoring_late_multiplier = 0.5

Early rounds worth 1.5x, normal rounds 1x, late rounds 0.5x.

API Endpoints
-------------

- ``GET /api/sla/dynamic-scoring`` - Current dynamic scoring configuration and multiplier


Combining SLA and Dynamic Scoring
=================================

Both features can be enabled simultaneously. The scoring flow is:

1. Base score calculated from successful checks
2. Dynamic scoring multiplier applied (if enabled)
3. SLA penalties deducted (if enabled)

This allows competitions to have complex scoring strategies that reward both uptime consistency and early performance.

Best Practices
==============

1. **Communication**: Clearly communicate SLA rules to teams before the competition
2. **Testing**: Test penalty calculations with your specific configuration before going live
3. **Monitoring**: Use the admin SLA dashboard to monitor penalty application
4. **Balance**: Choose penalty values that encourage uptime without being overly punitive
5. **Recovery**: Consider setting thresholds that allow teams reasonable time to recover
