#!/usr/bin/env bash
# Exit script if any commands fail and treat unset variables as errors
set -euo pipefail

cleanup() {
  echo "Cleaning up container environment"
  make stop-integration >/dev/null 2>&1 || true
  make clean-integration >/dev/null 2>&1 || true
}

trap cleanup EXIT

wait_for_container() {
  CONTAINER_NAME=$1
  SLEEP_AMOUNT=$2
  SLEEP_COMMAND_SCRIPT=${3:-}
  MAX_ATTEMPTS=${4:-0}
  ATTEMPTS=0
  while [ "$(docker inspect -f '{{.State.Running}}' "$CONTAINER_NAME")" = "true" ]
  do
    if [ -n "$SLEEP_COMMAND_SCRIPT" ]; then
      SLEEP_COMMAND_OUTPUT=$($SLEEP_COMMAND_SCRIPT)
      echo "$CONTAINER_NAME is not finished yet....sleeping for $SLEEP_AMOUNT seconds $SLEEP_COMMAND_OUTPUT"
    else
      echo "$CONTAINER_NAME is not finished yet....sleeping for $SLEEP_AMOUNT seconds"
    fi
    sleep $SLEEP_AMOUNT
    ATTEMPTS=$((ATTEMPTS + 1))
    if [ "$MAX_ATTEMPTS" -ne 0 ] && [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
      echo "Timeout waiting for $CONTAINER_NAME to finish"
      return 1
    fi
  done
}

wait_for_engine()
{
  get_engine_round() {
    local output
    if ! output=$(make -s integration-get-round 2>/dev/null); then
      echo 0
      return
    fi
    local round
    round=$(echo "$output" | sed -n 's/.*Round \([0-9]\+\).*/\1/p')
    if [ -z "$round" ]; then
      round=0
    fi
    echo "$round"
  }

  MAX_ATTEMPTS=${MAX_ENGINE_ATTEMPTS:-10}
  ATTEMPTS=0
  while [ "$(docker inspect -f '{{.State.Running}}' scoringengine-engine-1)" = "true" ]
  do
    ROUND=$(get_engine_round)
    echo "scoringengine-engine-1 is not finished yet....sleeping for 30 seconds (Round $ROUND)"
    sleep 30
    ATTEMPTS=$((ATTEMPTS + 1))
    if [ "$ATTEMPTS" -ge "$MAX_ATTEMPTS" ]; then
      echo "Timeout waiting for scoringengine-engine-1 to finish"
      docker logs scoringengine-engine-1 | tail -n 50 || true
      return 1
    fi
  done

  ROUND=$(get_engine_round)
  if [ "$ROUND" -eq 0 ]; then
    echo "scoringengine-engine-1 exited without producing a round"
    docker logs scoringengine-engine-1 | tail -n 50 || true
    return 1
  fi
}

# Stop any previous containers from other parts of testing
echo "Stopping any previous containers"
make stop-integration
make clean-integration

# Remove any stopped containers left over from previous runs
docker container prune -f >/dev/null 2>&1 || true

# Build and start the necessary containers
echo "Building required container environment"
make build build-integration
echo "Starting up required container environment"
make run-integration

# Wait for the bootstrap container to be done (meaning DB is setup)
wait_for_container "scoringengine-bootstrap-1" 10

# Sleep for a bit so that the engine has time to start up
# so that we can detect when it stops running
echo "Sleeping for 20 seconds for the engine to start up"
sleep 20

# Wait for engine to finish running
wait_for_engine

# Sleep for a bit so next MySQL call will return all results
echo "Sleeping for 5 seconds for MySQL to catch up"
sleep 5

# Run integration tests against live testbed db
echo "Running integration tests"
make run-integration-tests

