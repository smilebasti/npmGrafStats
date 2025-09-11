#!/bin/bash
# Get Reverse Proxy-host logs

# To better understand the collection with regular expression
# {1,3} get one to three characters. [0-9] character from to 0 to 9. \ for special characters. () grouping as an expression. | or
internalips="(10([\.][0-9]{1,3}){3})|(192.168([\.][0-9]{1,3}){2})|(172.(1[6-9]|2[0-9]|3[0-1])([\.][0-9]{1,3}){2})|(::1)|(f[cd][0-9a-fA-F]{2}:)|(fe[89ab][0-9a-fA-F]:)"
externalip=`curl -s ifconfig.me/ip`
echo "Your external IP is: $externalip"

# check if monitoringips.txt exists
if [ -f "/monitoringips.txt" ]
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

  # get time from logs
  measurementtime=`echo ${line:1:26} `
  #echo "measurement time: $measurementtime"

  # What does length say? 
  # save from 14 postion after space and only the first digits found to length 
  # length=`echo $line | awk -F ' ' '{print$14}' | grep --line-buffered -m 1 -o '[[:digit:]]*'`

  #Idea of getting device
  #device=`echo $line | grep -e ""'('*')'""`

  if [[ $outsideip == "127.0.0.1" ]]
  then
    continue
  elif [[ $outsideip =~ $internalips ]] || [[ $outsideip =~ $externalip ]]
  then
    echo "Internal IP-Source: $outsideip called: $targetdomain"
    if [ "$INTERNAL_LOGS" = "TRUE" ]
    then
      python /root/.config/NPMGRAF/Internalipinfo.py "$outsideip" "$targetdomain" "0" "InternalRProxyIPs" "$measurementtime"
    fi
  elif $monitorfile && grep --line-buffered -qFx $outsideip /monitoringips.txt
  then
    echo "An excluded monitoring service checked: $targetdomain"
    if [ "$MONITORING_LOGS" = "TRUE" ]
    then
      python /root/.config/NPMGRAF/Getipinfo.py "$outsideip" "$targetdomain" "0" "MonitoringRProxyIPs" "$measurementtime" "$asndb"
    fi
  else      
    python /root/.config/NPMGRAF/Getipinfo.py "$outsideip" "$targetdomain" "0" "ReverseProxyConnections" "$measurementtime" "$asndb"
  fi
done
}

for logfile in /nginx/access.log* /nginx/*_proxy.log; do
  process_logfile "$logfile" &
done

wait
