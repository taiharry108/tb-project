#!/bin/bash
source .env

sed -e s/POSTGRES_USER/${POSTGRES_USER}/g -e s/POSTGRES_PASSWORD/${POSTGRES_PASSWORD}/g core-repo/src/alembic.ini.template > core-repo/src/alembic.ini
sed -e s/POSTGRES_USER/${POSTGRES_USER}/g -e s/POSTGRES_PASSWORD/${POSTGRES_PASSWORD}/g ac-app/webapp/config.yml.template > ac-app/webapp/config.yml
sed -e s/POSTGRES_USER/${POSTGRES_USER}/g -e s/POSTGRES_PASSWORD/${POSTGRES_PASSWORD}/g auth-app/webapp/config.yml.template > auth-app/webapp/config.yml

mkdir -p core-repo/src/alembic/versions
