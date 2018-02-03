run:
	docker-compose -f docker-compose.yml -p scoring_engine up -d --scale flask=5

run-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -p scoring_engine up -d --scale flask=5

build:
	docker-compose -f docker-compose.yml -p scoring_engine build

build-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -p scoring_engine build

stop:
	docker-compose -f docker-compose.yml -p scoring_engine stop

stop-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -p scoring_engine stop

rm:
	docker-compose -f docker-compose.yml -p scoring_engine down -v --remove-orphans

rm-testbed:
	docker-compose -f docker-compose.yml -f docker/testbed/docker-compose.yml -p scoring_engine down -v --remove-orphans

rebuild: build stop run
rebuild-new: build stop rm run

rebuild-testbed: build-testbed stop-testbed run-testbed
rebuild-testbed-new: build-testbed stop-testbed rm-testbed run-testbed
