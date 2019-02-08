MAIN_DOCKER := docker-compose.yml
TESTBED_DOCKER := docker/testbed/docker-compose.yml
INTEGRATION_DOCKER := tests/integration/docker-compose.yml
PROJECT_NAME := scoringengine

GIT_HASH=$(shell git rev-parse --short HEAD)

.PHONY:all
all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]^\.PHONY.*].*:' Makefile

## Run Commands
.PHONY: run run-testbed run-integration run-integration-tests
run:
	SCORINGENGINE_VERSION=$(GIT_HASH) docker-compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) up -d
run-testbed:
	SCORINGENGINE_VERSION=$(GIT_HASH) docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -p $(PROJECT_NAME) up -d
run-integration:
	SCORINGENGINE_VERSION=$(GIT_HASH) docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) up -d
run-integration-tests:
	SCORINGENGINE_VERSION=$(GIT_HASH) docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) run tester bash -c "py.test --integration tests"

## Build Commands
.PHONY: build build-testbed build-integration
build:
	docker-compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) build
build-testbed:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -p $(PROJECT_NAME) build
build-integration:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) build

## Stop Commands
.PHONY: stop stop-testbed stop-integration
stop:
	docker-compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) stop
stop-testbed:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -p $(PROJECT_NAME) stop
stop-integration:
	docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) stop

## Clean Commands
.PHONY: clean clean-testbed clean-integration
clean:
	-docker-compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) down -v --remove-orphans
clean-testbed:
	-docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -p $(PROJECT_NAME) down -v --remove-orphans
clean-integration:
	-docker-compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) down -v --remove-orphans

## Rebuild Commands
.PHONY: rebuild rebuild-new rebuild-testbed rebuild-testbed-new rebuild-integration rebuild-integration-new
rebuild: build stop run
rebuild-new: build stop clean run
rebuild-testbed: build-testbed stop-testbed run-testbed
rebuild-testbed-new: build-testbed stop-testbed clean-testbed run-testbed
rebuild-integration: build-integration stop-integration run-integration
rebuild-integration-new: build-integration stop-integration clean-integration run-integration
