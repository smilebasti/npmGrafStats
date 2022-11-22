#!/bin/bash
echo "Startup: lets go and send connection info to influx"
sh $NPMGRAF_HOME/sendips.sh

sleep 0.5
tee $NPMGRAF_HOME/nohup.out > /proc/1/fd/1 2>/proc/1/fd/2
