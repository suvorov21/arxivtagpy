#!/bin/sh

SQL_HOST=postgres
SQL_PORT=5432
DATABASE=postgres

if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."

    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 1
    done

    echo "PostgreSQL started"
fi

exec "$@"