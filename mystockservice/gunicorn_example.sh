#!/usr/bin/env bash

#!/bin/bash
NAME=lucky # Name of the application
USER=yihan # the user to run as
GROUP=staff # the group to run as
NUM_WORKERS=4 # how many worker processes should Gunicorn spawn
TIMEOUT=600
WSGI_MODULE=lucky.main

echo "Starting $NAME as `whoami`"

exec pipenv run gunicorn ${WSGI_MODULE}:gunicorn_app \
--worker-class aiohttp.GunicornWebWorker \
--name $NAME \
--workers $NUM_WORKERS \
--timeout $TIMEOUT \
--user=$USER --group=$GROUP \
--bind=0.0.0.0:9001 \
--log-level=debug \
--log-file=-