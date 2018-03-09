#!/usr/bin/bash

cd /home/tparker/rsProcessing/trollduction
date
(time docker build -t junk2 --no-cache . > /dev/null ) 2>&1 | grep real | awk '{print $2}'
