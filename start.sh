#!/bin/bash
echo "npmGrafStats:plus-v3.0.1"
echo "Startup: lets get the logs send them to influx"

if [ -z "$INFLUX_TOKEN" ] && [ ! -f "/data/influxdb-token.txt" ]; then
    echo 'No InfluxDB Token as variable or in influxdb-token.txt file found.'
    echo 'Please add the Token. Exiting now.'
    exit 1
fi

bash /root/.config/NPMGRAF/sendips.sh

sleep 0.5
# reads from standard input and writes to standard output and in file
tee /root/.config/NPMGRAF/nohup.out > /proc/1/fd/1 2>/proc/1/fd/2

# Wait for any process to exit
wait -n
# Exit with status of process that exited first
exit $?
