#!/bin/sh

# cron is fussy about this
chmod 644 cron-mirrorGina

#systemctl stop mirrorGina.service && \

docker build -t datasources .
docker stop datasources 
docker rm datasources 
docker run --detach=true --volumes-from data --env-file=/home/tparker/private/datasources.env --name datasources datasources

