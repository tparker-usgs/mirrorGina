#!/bin/sh

#systemctl stop trollduction.service || docker stop trollduction
docker stop trollduction
docker rm trollduction 
docker build -t trollduction . && \
docker run --detach=true --volumes-from data --name trollduction trollduction
