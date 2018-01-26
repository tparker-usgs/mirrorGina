#!/bin/sh

# cron is fussy about this
chmod 644 cron-collectors

#systemctl stop mirrorGina.service && \

docker build -t collectors1 .
docker stop collectors3
docker rm collectors3
docker run --detach=true --volumes-from data --env-file=/home/tparker/private/collectors.env --name collectors1 collectors1

