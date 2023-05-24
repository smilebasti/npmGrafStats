#!/bin/bash
echo "Startup: lets get logs data and send them to influx"


if [ "$REDIRECTION_LOGS" = "TRUE" ]
then
    echo "Redirection Logs activated"
    bash /root/.config/NPMGRAF/sendips.sh &
    bash /root/.config/NPMGRAF/sendredirectionips.sh &
    
else
    echo "Redirection Logs deactivated"
    bash /root/.config/NPMGRAF/sendips.sh
fi

sleep 0.5
# reads from standard input and writes to standard output and in file
tee /root/.config/NPMGRAF/nohup.out > /proc/1/fd/1 2>/proc/1/fd/2

# Wait for any process to exit
wait -n
# Exit with status of process that exited first
exit $?
