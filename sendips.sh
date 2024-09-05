#!/bin/bash
# Get Reverse Proxy-host logs

# To better understand the collection with regular expression
# {1,3} get one to three characters. [0-9] character from to 0 to 9. \ for special characters. () grouping as an expression. | or
internalips="(10([\.][0-9]{1,3}){3})|(192.168([\.][0-9]{1,3}){2})|(172.(1[6-9]|2[0-9]|3[0-1])([\.][0-9]{1,3}){2})"
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
tail -F /logs/proxy-host-*_access.log | grep --line-buffered -E "([0-9]{1,3}[\.]){3}[0-9]{1,3}" | while read line;

do
  # Domain or subdomain gets found.
  targetdomain=`echo $line | grep --line-buffered -m 1 -o -E "([a-z0-9\-]*\.){1,3}?[a-z0-9\-]*\.[A-Za-z]{2,6}" | head -1`

  # Get the first ip found = outsideip
  # head -1 because grep finds two (sometimes three) and only the first is needed
  outsideip=`echo $line | grep --line-buffered -o -m 1 -E "(([0-9]{1,3}[\.]){3}[0-9]{1,3}|([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))" | head -1` 

  # head -2 and tail -1 because grep finds two (sometimes three) and only the second is needed
  targetip=`echo $line | grep --line-buffered -o -m 1 -E "(([0-9]{1,3}[\.]){3}[0-9]{1,3}|([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))" | head -2| tail -1` 

  # What does length say? 
  # save from 14 postion after space and only the first digits found to length 
  length=`echo $line | awk -F ' ' '{print$14}' | grep --line-buffered -m 1 -o '[[:digit:]]*'`

  # get time from logs
  measurementtime=`echo ${line:1:26} `
  #echo "measurement time: $measurementtime"

  #Idea of getting device
  #device=`echo $line | grep -e ""'('*')'""`

  if [[ $outsideip =~ $internalips ]] || [[ $outsideip =~ $externalip ]]
  then
    echo "Internal IP-Source: $outsideip called: $targetdomain"
    if [ "$INTERNAL_LOGS" = "TRUE" ]
    then
      python /root/.config/NPMGRAF/Internalipinfo.py "$outsideip" "$targetdomain" "$length" "$targetip" "InternalRProxyIPs" "$measurementtime"
    fi
  elif $monitorfile && grepcidr -D $outsideip /monitoringips.txt >> /dev/nul
  then
    echo "An excluded monitoring service checked: $targetdomain"
    if [ "$MONITORING_LOGS" = "TRUE" ]
    then
      python /root/.config/NPMGRAF/Getipinfo.py "$outsideip" "$targetdomain" "$length" "$targetip" "MonitoringRProxyIPs" "$measurementtime" "$asndb"
    fi
  else      
    python /root/.config/NPMGRAF/Getipinfo.py "$outsideip" "$targetdomain" "$length" "$targetip" "ReverseProxyConnections" "$measurementtime" "$asndb"
  fi
done
reboot
