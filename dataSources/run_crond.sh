#!/bin/bash

# prepend application environment variables to crontab
env | grep -v PATH | cat - /tmp/cron-mirrorGina > /etc/cron.d/cron-mirrorGina

/usr/sbin/cron -f /app/mirrorGina/cron-mirrorGina
