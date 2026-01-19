#!/bin/bash
# Get Reverse Proxy-host logs

# To better understand the collection with regular expression
# {1,3} get one to three characters. [0-9] character from to 0 to 9. \ for special characters. () grouping as an expression. | or
internalips="(10([\.][0-9]{1,3}){3})|(192.168([\.][0-9]{1,3}){2})|(172.(1[6-9]|2[0-9]|3[0-1])([\.][0-9]{1,3}){2}) |(::1)|(f[cd][0-9a-fA-F]{2}:)|(fe[89ab][0-9a-fA-F]:)"
externalip=`curl -s ifconfig.me/ip`
echo "Your external IP is: $externalip"

MONITOR_FILE_PATH="/data/monitoringips.txt"

# check if monitoringips.txt exists
if [ -f "$MONITOR_FILE_PATH" ]
then
  monitorfile=true
else 
  monitorfile=false
fi
# check if ASN DB exists
if [ -f "/geolite/GeoLite2-ASN.mmdb" ]
then
  asndb=true
else 
  asndb=false
fi

# gets all lines including an IP. 
# Grep finds the the IP addresses in the access.log
process_logfile(){
tail --follow=name --retry "$logfile" | grep --line-buffered -v "localhost" | while read line;

do
  # Domain or subdomain gets found.
  targetdomain=`echo $line | cut -d' ' -f3`
  # The above cuts the echo output with a space delimiter (-d' ') and outputs the thrid field (-f3)

  # Get the first ip found = outsideip
  outsideip=`echo $line | cut -d' ' -f4`

  # Status Code
  statuscode=`echo $line | cut -d' ' -f9`

  # get time from logs
  measurementtime=`echo ${line:1:26} `

  # length bytes transferd
  length=`echo $line | cut -d' ' -f11`

  # Extract User-Agent
  useragent=`echo $line | cut -d' ' -f13-`

  if [[ $outsideip == "127.0.0.1" ]]
  then
    continue
  elif [[ $outsideip =~ $internalips ]] || [[ $outsideip =~ $externalip ]]
  then
    echo "Internal IP-Source: $outsideip called: $targetdomain"
    if [ "$INTERNAL_LOGS" = "TRUE" ]
    then
      python /home/appuser/.config/NPMGRAF/Internalipinfo.py "$outsideip" "$targetdomain" "$length" "InternalRProxyIPs" "$measurementtime" "$statuscode" "$useragent"
    fi
  elif $monitorfile && grepcidr -D $outsideip $MONITOR_FILE_PATH >> /dev/null
  then
    echo "An excluded monitoring service checked: $targetdomain"
    if [ "$MONITORING_LOGS" = "TRUE" ]
    then
      python /home/appuser/.config/NPMGRAF/Getipinfo.py "$outsideip" "$targetdomain" "$length" "MonitoringRProxyIPs" "$measurementtime" "$asndb" "$statuscode" "$useragent"
    fi
  else      
    python /home/appuser/.config/NPMGRAF/Getipinfo.py "$outsideip" "$targetdomain" "$length" "ReverseProxyConnections" "$measurementtime" "$asndb" "$statuscode" "$useragent"
  fi
done
}

for logfile in /nginx/access.log* /nginx/*_proxy.log; do
  process_logfile "$logfile" &
done

wait