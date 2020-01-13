#!make

superset-build:
	DOCKER_BUILDKIT=1 BUILDKIT_PROGRESS=plain docker build -f docker/superset/Dockerfile-local -t "superset:local" --build-arg SUPERSET_BRANCH=${SUPERSET_BRANCH} --build-arg SUPERSET_LATEST_COMMIT=${SUPERSET_LATEST_COMMIT} ..

superset-down:
	cd docker && docker-compose down

superset-create-admin:
	cd docker && docker-compose run --rm superset superset/docker-init.sh

superset-up:
	cd docker && docker-compose up
