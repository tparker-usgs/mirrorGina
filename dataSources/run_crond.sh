#!/bin/bash

# prepend application environment variables to crontab
env | grep -v PATH | cat - /tmp/cron-dataSources > /etc/cron.d/cron-dataSources

/usr/sbin/cron -f 
