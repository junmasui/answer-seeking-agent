#!/bin/sh

[ -z "$POSTGRES_HOST" ] && echo "missing POSTGRES_HOST" && exit -1
[ -z "$POSTGRES_USER" ] && echo "missing POSTGRES_USER" && exit -1
[ -z "$POSTGRES_PASSWORD" ] && echo "missing POSTGRES_PASSWORD" && exit -1
[ -z "$BACKEND_POSTGRES_USER_PASSWORD" ] && echo "missing BACKEND_POSTGRES_USER_PASSWORD" && exit -1

export PGPASSWORD=$POSTGRES_PASSWORD

envsubst < /init-db.sql.template > /init-db.sql
sleep 10
psql -h pgvector -U $POSTGRES_USER -f /init-db.sql
