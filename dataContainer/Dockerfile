# volume container
# ecapsulates acces to the local filesystem. Used in both data mirroring
# and product generation 
 
# BUILD-USING:        docker build -t data .
# RUN-USING:          docker run  -d -v /data:/data --name data data
# INSPECT-USING:      docker run -t -i  --volumes-from data ubuntu:latest /bin/bash

FROM stackbrew/busybox:latest

# Create logs volume
VOLUME /data
WORKDIR /data/logs

CMD  ["true"]
