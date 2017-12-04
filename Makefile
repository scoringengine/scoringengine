run:
	docker-compose -f docker/docker-compose.yml -p scoring_engine up -d

build:
	docker-compose -f docker/docker-compose.yml -p scoring_engine build

stop:
	docker-compose -f docker/docker-compose.yml -p scoring_engine stop

rebuild: build stop run
