#!make

superset-build:
	DOCKER_BUILDKIT=1 BUILDKIT_PROGRESS=plain docker build -f docker/superset/Dockerfile -t "superset:prod" ..

superset-down:
	cd docker && docker-compose down

superset-create-admin:
	cd docker && docker-compose run --rm superset docker-init.sh

superset-up:
	cd docker && docker-compose up
