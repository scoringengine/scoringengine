run:
	docker-compose -f docker/docker-compose.yml -p scoring_engine up -d

build:
	docker-compose -f docker/docker-compose.yml -p scoring_engine build

stop:
	docker-compose -f docker/docker-compose.yml -p scoring_engine stop

rm:
	docker-compose -f docker/docker-compose.yml -p scoring_engine down -v --remove-orphans

rebuild: build stop run
rebuild-new: build stop rm run