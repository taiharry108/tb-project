include .env

COMPOSE_FILE := ./auth-app-home/docker-compose.yml
SRC_DIR := ./ac-app/webapp

gen-key:
	@ssh-keygen -q -t rsa -b 4096 -m PEM -f jwt.key -N ""
	@openssl rsa -in jwt.key -pubout -outform PEM -out jwt.key.pub

build:
	@docker compose -f ${COMPOSE_FILE} build

run:
	@export POSTGRES_PASSWORD=${POSTGRES_PASSWORD} && \
		export POSTGRES_USER=${POSTGRES_USER} && \
		export DB_URL=${DB_URL} && \
		export REDIS_URL=${REDIS_URL} && \
		docker compose -f ${COMPOSE_FILE} up web
build-client:
	@docker compose -f ${COMPOSE_FILE} run --rm frontend npm run start

migrate-db:
	@export POSTGRES_PASSWORD=${POSTGRES_PASSWORD} && \
		export POSTGRES_USER=${POSTGRES_USER} && \
		docker compose -f ${COMPOSE_FILE} run --rm core alembic revision --autogenerate -m '${MIGRATION_MESSAGE}' && \
		docker compose -f ${COMPOSE_FILE} run --rm core alembic upgrade head

update-db:
	@docker compose -f ./ac-app/docker-compose.yml run --rm web /bin/sh -c "openvpn \
		--config /openvpn/client.ovpn --auth-user-pass /openvpn/pass.txt & python update_chapter_meta.py"

run-lint:
	@docker compose run --rm tool black .

export-history:
	@docker compose -f ./ac-app/docker-compose.yml run --rm web python export_history.py

run-tests:
	@export JWT_PUBLIC_KEY=${JWT_PUBLIC_KEY} && \
		export COMPOSE_FILE=${COMPOSE_FILE} && \
		export POSTGRES_PASSWORD=${POSTGRES_PASSWORD} && \
		export POSTGRES_USER=${POSTGRES_USER} && \
		export DB_URL=${TEST_DB_URL} && \
		export REDIS_URL=${REDIS_URL} && \
		./run_tests.sh
