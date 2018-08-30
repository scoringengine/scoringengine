run:
	docker-compose -f docker-compose.yml -p scoringengine up -d

run-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -p scoringengine up -d

build:
	docker-compose -f docker-compose.yml -p scoringengine build

build-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -p scoringengine build

stop:
	docker-compose -f docker-compose.yml -p scoringengine stop

stop-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -p scoringengine stop

rm:
	docker-compose -f docker-compose.yml -p scoringengine down -v --remove-orphans

rm-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -p scoringengine down -v --remove-orphans

rebuild: build stop run
rebuild-new: build stop rm run

rebuild-testbed: build-testbed stop-testbed run-testbed
rebuild-testbed-new: build-testbed stop-testbed rm-testbed run-testbed
