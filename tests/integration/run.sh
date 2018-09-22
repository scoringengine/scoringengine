# Exit script if any commands fail
set -e

wait_for_container()
{
  CONTAINER_NAME=$1
  SLEEP_AMOUNT=$2
  echo "Waiting for $CONTAINER_NAME container to finish"
  while [ "`docker inspect -f {{.State.Running}} $CONTAINER_NAME`" == "true" ]
  do
    echo "Not finished....sleeping for $SLEEP_AMOUNT seconds"
    sleep $SLEEP_AMOUNT
  done
}


# Stop any previous containers from other parts of testing
echo "Stopping any previous containers"
docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -f tests/integration/docker-compose.yml -p scoringengine down -v --remove-orphans

# Build and start the necessary containers
echo "Building required container environment"
docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -f tests/integration/docker-compose.yml -p scoringengine build
echo "Starting up required container environment"
docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -f tests/integration/docker-compose.yml -p scoringengine up -d

# Wait for the bootstrap container to be done (meaning DB is setup)
wait_for_container "scoringengine_bootstrap_1" 5

# Modify some settings on the fly so we don't have to wait so long
echo "Modifying some settings on the fly"
docker run -it --network=scoringengine_default scoringengine_tester bash -c "python /app/tests/integration/update_settings.py"

# Wait for engine to finish running
wait_for_container "scoringengine_engine_1" 10

# Run integration tests against live testbed db
echo "Running integration tests"
docker run -it --network=scoringengine_default scoringengine_tester bash -c "py.test --integration tests"
