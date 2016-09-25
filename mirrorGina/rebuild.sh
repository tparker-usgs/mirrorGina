#!/bin/sh

# cron is fussy about this
chmod 644 cron-mirrorGina

systemctl stop mirrorGina.service && \
docker stop mirrorgina && \
docker rm mirrorgina && \
docker build -t mirrorgina . && \
docker run --detach=true --volumes-from data --name mirrorgina mirrorgina
