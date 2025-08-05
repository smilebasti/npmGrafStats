#!/bin/bash
echo "npmGrafStats: v2.4.3"
echo "Startup: lets get the logs send them to influx"


if [ "$REDIRECTION_LOGS" = "TRUE" ]
then
    echo "Redirection and Reverse-Proxy Logs activated"
    bash /root/.config/NPMGRAF/sendips.sh &
    bash /root/.config/NPMGRAF/sendredirectionips.sh &

elif [ "$REDIRECTION_LOGS" = "ONLY" ]
then
    echo "Only Redirection Logs activated"
    bash /root/.config/NPMGRAF/sendredirectionips.sh

else
    echo "Only Reverse-Proxy Logs activated"
    bash /root/.config/NPMGRAF/sendips.sh
fi

sleep 0.5
# reads from standard input and writes to standard output and in file
tee /root/.config/NPMGRAF/nohup.out > /proc/1/fd/1 2>/proc/1/fd/2

# Wait for any process to exit
wait -n
# Exit with status of process that exited first
exit $?
