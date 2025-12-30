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
echo "Waiting for bootstrap to complete database initialization"
docker compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -f tests/integration/docker-compose.yml -p scoringengine wait bootstrap

# Wait for engine to become healthy (meaning it has started and can query the database)
echo "Waiting for engine to start and become healthy"
docker compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -f tests/integration/docker-compose.yml -p scoringengine wait engine

# Wait for engine to finish running (it will exit after NUM_ROUNDS)
echo "Waiting for engine to complete all rounds"
wait_for_engine

# Run integration tests against live testbed db
echo "Running integration tests"
make run-integration-tests

# Clean up container environment
echo "Cleaning up container environment"
make stop-integration
