# Exit script if any commands fail
set -e

wait_for_container()
{
  CONTAINER_NAME=$1
  SLEEP_AMOUNT=$2
  SLEEP_COMMAND_SCRIPT=$3
  while [ "`docker inspect -f {{.State.Running}} $CONTAINER_NAME`" == "true" ]
  do
    SLEEP_COMMAND_OUTPUT=$($SLEEP_COMMAND_SCRIPT)
    echo "$CONTAINER_NAME is not finished yet....sleeping for $SLEEP_AMOUNT seconds $SLEEP_COMMAND_OUTPUT"
    sleep $SLEEP_AMOUNT
  done
}

wait_for_engine()
{
  wait_for_container "scoringengine-engine-1" 30 "make -s integration-get-round"
}

wait_for_engine_healthy()
{
  echo "Waiting for engine to start and become healthy"
  COMPOSE_CMD="docker compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -f tests/integration/docker-compose.yml -p scoringengine"

  # Wait up to 60 seconds for engine to become healthy
  for i in $(seq 1 12); do
    HEALTH_STATUS=$($COMPOSE_CMD ps engine --format json | grep -o '"Health":"[^"]*"' | cut -d'"' -f4 || echo "starting")
    if [ "$HEALTH_STATUS" = "healthy" ]; then
      echo "Engine is healthy and ready"
      return 0
    fi
    echo "Engine health status: $HEALTH_STATUS, waiting... (attempt $i/12)"
    sleep 5
  done

  echo "Warning: Engine did not become healthy within 60 seconds, proceeding anyway"
  return 0
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

# Bootstrap completion is handled by engine's depends_on: bootstrap (service_completed_successfully)
# So we just need to wait for engine to become healthy, then wait for it to complete

# Wait for engine to become healthy (meaning it has started and can query the database)
wait_for_engine_healthy

# Wait for engine to finish running (it will exit after NUM_ROUNDS)
echo "Waiting for engine to complete all rounds"
wait_for_engine

# Run integration tests against live testbed db
echo "Running integration tests"
make run-integration-tests

# Clean up container environment
echo "Cleaning up container environment"
make stop-integration
