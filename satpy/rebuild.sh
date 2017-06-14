#!/bin/sh

#systemctl stop trollduction.service || docker stop trollduction
docker build -t satpy .
docker stop satpy
docker rm satpy
docker run --detach=true --volumes-from data --env-file=/home/tparker/private/satpy.env --name satpy satpy
