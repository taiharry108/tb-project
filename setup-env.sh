#!/bin/bash
source .env
make gen-key
docker network create demo_net
sed -e s/POSTGRES_USER/${POSTGRES_USER}/g -e s/POSTGRES_PASSWORD/${POSTGRES_PASSWORD}/g core-repo/src/alembic.ini.template > core-repo/src/alembic.ini
cp ac-app/webapp/config.yml.template ac-app/webapp/config.yml
cp auth-app/webapp/config.yml.template auth-app/webapp/config.yml

mkdir -p core-repo/src/alembic/versions
