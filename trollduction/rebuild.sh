#!/bin/sh

# cron is fussy about this
chmod 644 cron-mirrorGina

systemctl stop trollduction.service && \
docker stop trollduction && \
docker rm trollduction && \
docker build -t trollduction . && \
docker run --detach=true --volumes-from data --name trollduction trollduction
