#!/bin/bash

# gets all lines including an IP. 
#Grep finds the the IP addresses without the HOME_IPS in the access.log
tail -f /logs/proxy-host*access.log | grep --line-buffered -E "([0-9]{1,3}[\.]){3}[0-9]{1,3}" | grep --line-buffered -v "$HOME_IPS" | while read line;

do
  #Domain or subdomain gets found. only de/net/org/com
  targetdomain=`echo $line | grep -m 1 -o -E "([a-z0-9\-]*\.){1,3}?[a-z0-9\-]*\.[A-Za-z]{2,6}" | head -1`

  #Get the first ip found = outsideip
  # head -1 because grep finds two (sometimes three) and only the first is needed
  outsideip=`echo $line | grep -o -m 1 -E "(([0-9]{1,3}[\.]){3}[0-9]{1,3}|([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))" | head -1` 


  # head -2 and tail -1 because grep finds two (sometimes three) and only the second is needed
  targetip=`echo $line | grep -o -m 1 -E "(([0-9]{1,3}[\.]){3}[0-9]{1,3}|([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,7}:|([0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|([0-9a-fA-F]{1,4}:){1,5}(:[0-9a-fA-F]{1,4}){1,2}|([0-9a-fA-F]{1,4}:){1,4}(:[0-9a-fA-F]{1,4}){1,3}|([0-9a-fA-F]{1,4}:){1,3}(:[0-9a-fA-F]{1,4}){1,4}|([0-9a-fA-F]{1,4}:){1,2}(:[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:((:[0-9a-fA-F]{1,4}){1,6})|:((:[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(:[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(ffff(:0{1,4}){0,1}:){0,1}((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])|([0-9a-fA-F]{1,4}:){1,4}:((25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(25[0-5]|(2[0-4]|1{0,1}[0-9]){0,1}[0-9]))" | head -2| tail -1` 

  # What does length say? 
  # save from 14 postion after space and only the first digits found to length 
  length=`echo $line | awk -F ' ' '{print$14}' | grep -m 1 -o '[[:digit:]]*'`

  #if [ -z "$domain" ] 
  #then
  #domain="No Domain called"
  #else
  #domain = `echo $domain | head -1`
  #fi
  
  #Idea of getting device
  #device=`echo $line | grep -e ""'('*')'""`

  #check if domain is empty but if found use the first found
  #if [ -z "$domain" ] 
  #then
  #  targetdomain="No Domain called"
  #else
  #  targetdomain=`echo $domain | grep -m 1 -o -E "([a-z0-9\-]*\.){1,3}?[a-z0-9\-]*\.(de|net|org|com)" | head -1`
  #fi

  # prints to log what is transferd to Getipinfo.py
  #echo $length #argv 3
  #echo $outsideip # argv 1
  #echo $targetip # argv 4
  #echo $domain
  #echo $targetdomain # argv 2


  python /root/.config/NPMGRAF/Getipinfo.py "$outsideip" "$targetdomain" "$length" "$targetip"

done
reboot

