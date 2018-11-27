MAIN_DOCKER := docker-compose.yml
TESTBED_DOCKER := docker/testbed/docker-compose.yml
INTEGRATION_DOCKER := tests/integration/docker-compose.yml
PROJECT_NAME := scoringengine


run:
	docker-compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) up -d

run-testbed:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -p $(PROJECT_NAME) up -d

run-integration:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) up -d

run-integration-tests:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) run tester bash -c "py.test --integration tests"

build:
	docker-compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) build

build-testbed:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -p $(PROJECT_NAME) build

build-integration:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) build

stop:
	docker-compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) stop

stop-testbed:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -p $(PROJECT_NAME) stop

stop-integration:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) stop

rm:
	docker-compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) down -v --remove-orphans

rm-testbed:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -p $(PROJECT_NAME) down -v --remove-orphans

rm-integration:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) down -v --remove-orphans

rebuild: build stop run
rebuild-new: build stop rm run

rebuild-testbed: build-testbed stop-testbed run-testbed
rebuild-testbed-new: build-testbed stop-testbed rm-testbed run-testbed

rebuild-integration: build-integration stop-integration run-integration
rebuild-integration-new: build-integration stop-integration rm-integration run-integration
