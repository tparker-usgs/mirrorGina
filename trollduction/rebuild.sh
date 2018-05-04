#!/bin/sh

#systemctl stop trollduction.service || docker stop trollduction
docker rm trollduction-old
docker rename trollduction trollduction-old
docker build -t trollduction . 
docker stop trollduction-old
docker run --restart=always --detach=true --volumes-from data --env-file=/home/tparker/private/trollduction.env --name trollduction trollduction
