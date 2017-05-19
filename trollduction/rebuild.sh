#!/bin/sh

#systemctl stop trollduction.service || docker stop trollduction
docker build -t trollduction . 
docker stop trollduction
docker rm trollduction 
docker run --detach=true --volumes-from data --env-file=/home/tparker/private/trollduction.env --name trollduction trollduction
