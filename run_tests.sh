#!/bin/bash
docker compose -f ${COMPOSE_FILE} up -d test-db --scale test-db=1
docker compose -f ${COMPOSE_FILE} run --rm web-test pytest -ras -s .
docker compose -f ${COMPOSE_FILE} down test-db
