#!/bin/bash
echo "npmGrafStats: v3.1.0-pre"
echo "Startup: lets get the logs send them to influx"

if [ -z "$INFLUX_TOKEN" ] && [ ! -f "/data/influxdb-token.txt" ]; then
    echo 'No InfluxDB Token as variable or in influxdb-token.txt file found.'
    echo 'Please add the Token. Exiting now.'
    exit 1
fi

if [ "$REDIRECTION_LOGS" = "TRUE" ]
then
    echo "Redirection and Reverse-Proxy Logs activated"
    bash /home/appuser/.config/NPMGRAF/sendips.sh &
    bash /home/appuser/.config/NPMGRAF/sendredirectionips.sh &

elif [ "$REDIRECTION_LOGS" = "ONLY" ]
then
    echo "Only Redirection Logs activated"
    bash /home/appuser/.config/NPMGRAF/sendredirectionips.sh

else
    echo "Only Reverse-Proxy Logs activated"
    bash /home/appuser/.config/NPMGRAF/sendips.sh
fi

sleep 0.5
# reads from standard input and writes to standard output and in file
tee /home/appuser/.config/NPMGRAF/nohup.out > /proc/1/fd/1 2>/proc/1/fd/2

# Wait for any process to exit
wait -n
# Exit with status of process that exited first
exit $?
