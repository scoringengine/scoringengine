MAIN_DOCKER := docker-compose.yml
TESTBED_DOCKER := docker/testbed/docker-compose.yml
INTEGRATION_DOCKER := tests/integration/docker-compose.yml
TESTS_DOCKER:= tests/docker-compose.yml
PROJECT_NAME := scoringengine
BUILD_MODE	:= build  ## Pass `pull` in order to pull images instead of building them

GIT_HASH=$(shell git rev-parse --short HEAD)

.PHONY:all
all:
	@echo 'Available make targets:'
	@grep '^[^#[:space:]^\.PHONY.*].*:' Makefile

## Run Commands
.PHONY: run run-tests run-testbed run-integration run-integration-tests run-demo
run:
	SCORINGENGINE_VERSION=$(GIT_HASH) docker compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) up -d
run-tests:
	# docker compose -f $(TESTS_DOCKER) -p $(PROJECT_NAME) up -d
	# Flake8 checks
	# docker run -i scoringengine/tester bash -c "flake8 --config .flake8 ./"
	# Run unit tests
	# docker run -i -v artifacts:/app/artifacts scoringengine/tester bash -c "py.test --cov=scoring_engine --cov-report=xml:/app/artifacts/coverage.xml tests"
	coverage run --source=scoring_engine -m pytest -v tests/
run-testbed:
	SCORINGENGINE_VERSION=$(GIT_HASH) docker compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -p $(PROJECT_NAME) up -d
run-integration:
	SCORINGENGINE_VERSION=$(GIT_HASH) docker compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) up -d
run-integration-tests:
	SCORINGENGINE_VERSION=$(GIT_HASH) docker compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) run tester bash -c "py.test --integration tests"
run-demo:
	SCORINGENGINE_EXAMPLE=true SCORINGENGINE_OVERWRITE_DB=true SCORINGENGINE_VERSION=$(GIT_HASH) docker compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) up -d


## Build Commands
.PHONY: build build-tests build-testbed build-integration
build:
	docker compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) $(BUILD_MODE) base
	docker compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) $(BUILD_MODE) --parallel
build-tests:
	docker compose -f $(MAIN_DOCKER) -f $(TESTS_DOCKER) -p $(PROJECT_NAME) $(BUILD_MODE) base
	docker compose -f $(MAIN_DOCKER) -f $(TESTS_DOCKER) -p $(PROJECT_NAME) $(BUILD_MODE) tester redis
build-testbed:
	docker compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -p $(PROJECT_NAME) $(BUILD_MODE) --parallel
build-integration:
	docker compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) $(BUILD_MODE) --parallel

## Stop Commands
.PHONY: stop stop-tests stop-testbed stop-integration
stop:
	docker compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) stop
stop-tests:
	docker compose -f $(MAIN_DOCKER) -f $(TESTS_DOCKER) -p $(PROJECT_NAME) stop
stop-testbed:
	docker compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -p $(PROJECT_NAME) stop
stop-integration:
	docker compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) stop

## Clean Commands
.PHONY: clean clean-testbed clean-integration
clean:
	docker compose -f $(MAIN_DOCKER) -p $(PROJECT_NAME) down -v --remove-orphans
clean-testbed:
	docker compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -p $(PROJECT_NAME) down -v --remove-orphans
clean-integration:
	docker compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) down -v --remove-orphans

## Rebuild Commands
.PHONY: rebuild rebuild-new rebuild-tests rebuild-testbed rebuild-testbed-new rebuild-integration rebuild-integration-new
rebuild: build stop run
rebuild-new: build stop clean run
rebuild-tests: build-tests stop-tests run-tests
rebuild-testbed: build-testbed stop-testbed run-testbed
rebuild-testbed-new: build-testbed stop-testbed clean-testbed run-testbed
rebuild-integration: build-integration stop-integration run-integration
rebuild-integration-new: build-integration stop-integration clean-integration run-integration

.PHONY: integration-get-round
integration-get-round:
	docker compose -f $(MAIN_DOCKER) -f $(TESTBED_DOCKER) -f $(INTEGRATION_DOCKER) -p $(PROJECT_NAME) run --no-deps engine bash -c "python -c 'from scoring_engine.models.round import Round; print(\"(Round {0})\".format(Round.get_last_round_num()))'"
