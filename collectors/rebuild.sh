#!/bin/sh

# cron is fussy about this
chmod 644 cron-mirrorGina

#systemctl stop mirrorGina.service && \

docker build -t collectors .
docker stop collectors 
docker rm collectors 
docker run --detach=true --volumes-from data --env-file=/home/tparker/private/collectors.env --name collectors collectors

