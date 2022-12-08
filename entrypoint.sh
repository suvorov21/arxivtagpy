#!/bin/sh

SQL_HOST=postgres
SQL_PORT=5432
DATABASE=postgres

# Create environment of none
if [ ! -f .env ]
then
 cp .env_example .env
fi

# build frontend
cd app/frontend/src/
npm install
npm run build
cd ../../../


# wait for DB start
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 1
    done

    echo "PostgreSQL started"
fi

exec "$@"