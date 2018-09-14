run:
	docker-compose -f docker-compose.yml up -d

run-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml up -d

build:
	docker-compose -f docker-compose.yml build

build-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml build

stop:
	docker-compose -f docker-compose.yml stop

stop-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml stop

rm:
	docker-compose -f docker-compose.yml down -v --remove-orphans

rm-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml down -v --remove-orphans

rebuild: build stop run
rebuild-new: build stop rm run

rebuild-testbed: build-testbed stop-testbed run-testbed
rebuild-testbed-new: build-testbed stop-testbed rm-testbed run-testbed
