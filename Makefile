run:
	docker-compose -f docker-compose.yml up -d

run-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml up -d

run-integration:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -f tests/integration/docker-compose.yml up -d

build:
	docker-compose -f docker-compose.yml build

build-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml build

build-integration:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -f tests/integration/docker-compose.yml build

stop:
	docker-compose -f docker-compose.yml stop

stop-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml stop

stop-integration:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -f tests/integration/docker-compose.yml stop

rm:
	docker-compose -f docker-compose.yml down -v --remove-orphans

rm-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml down -v --remove-orphans

rm-integration:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -f tests/integration/docker-compose.yml down -v --remove-orphans

rebuild: build stop run
rebuild-new: build stop rm run

rebuild-testbed: build-testbed stop-testbed run-testbed
rebuild-testbed-new: build-testbed stop-testbed rm-testbed run-testbed

rebuild-integration: build-integration stop-integration run-integration
rebuild-integration-new: build-integration stop-integration rm-integration run-integration
