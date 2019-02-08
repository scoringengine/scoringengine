# Exit script if any commands fail
set -e

wait_for_container()
{
  CONTAINER_NAME=$1
  SLEEP_AMOUNT=$2
  while [ "`docker inspect -f {{.State.Running}} $CONTAINER_NAME`" == "true" ]
  do
    echo "$CONTAINER_NAME is not finished yet....sleeping for $SLEEP_AMOUNT seconds"
    sleep $SLEEP_AMOUNT
  done
}


# Stop any previous containers from other parts of testing
echo "Stopping any previous containers"
make stop-integration
make clean-integration

# Build and start the necessary containers
echo "Building required container environment"
make build-integration
echo "Starting up required container environment"
make run-integration

# Wait for the bootstrap container to be done (meaning DB is setup)
wait_for_container "scoringengine_bootstrap_1" 10

# Sleep for a bit so that the engine has time to start up
# so that we can detect when it stops running
echo "Sleeping for 20 seconds for the engine to start up"
sleep 20

# Wait for engine to finish running
wait_for_container "scoringengine_engine_1" 30

# Sleep for a bit so next MySQL call will return all results
echo "Sleeping for 5 seconds for MySQL to catch up"
sleep 5

# Run integration tests against live testbed db
echo "Running integration tests"
make run-integration-tests

# Clean up container environment
echo "Cleaning up container environment"
make stop-integration
