#!/bin/sh

# cron is fussy about this
chmod 644 cron-mirrorGina

#systemctl stop mirrorGina.service && \

docker build -t mirrorgina .
docker stop mirrorgina 
docker rm mirrorgina 
docker run --detach=true --volumes-from data --env-file=/home/tparker/private/mirrorgina.env --name mirrorgina mirrorgina

