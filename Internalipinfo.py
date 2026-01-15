#!/usr/bin/python3

import sys
import os
import socket
import time
from datetime import datetime, timedelta
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS
from ua_parser import user_agent_parser

print ('**************** start *********************')
measurement_name = (sys.argv[5]) # get measurement from argv
print ('Measurement-name: '+measurement_name) 

# Configuration for Persistent Data
DATA_DIR = "/data"
INFLUX_TOKEN_FILE = os.path.join(DATA_DIR, "influxdb-token.txt")

# argv[1] = outsideip, agrv[2] = Domain, argv[3] length, argv[4] tragetip, sys.argv[5] bucketname, sys.argv[6] date, sys.argv[7] statuscode, sys.argv[8] useragent
IP = str(sys.argv[1])
Domain = str(sys.argv[2])
length = int(sys.argv[3])
Target = str(sys.argv[4])
statuscode = int(sys.argv[7])
useragent = str(sys.argv[8])

# Parse User-Agent
parsed_ua = user_agent_parser.Parse(useragent)
browser = parsed_ua['user_agent']['family'] or 'Unknown'
browser_only_version = parsed_ua['user_agent']['major'] or '0'
browser_version = browser + ": " + browser_only_version
if parsed_ua['user_agent']['minor']:
    browser_version += '.' + parsed_ua['user_agent']['minor']
os_family = parsed_ua['os']['family'] or 'Unknown'

# print to log
print ('Calling IP: ', IP)
print ('Target IP: ', Target)
print ('Domain: ', Domain)
print ('Statuscode ', statuscode)
print("Browser Version:", browser_version)
print("OS Family:", os_family)

## get env vars and use

ifhost = os.getenv('INFLUX_HOST')
ifbucket = os.getenv('INFLUX_BUCKET')
iforg    = os.getenv('INFLUX_ORG')

if os.getenv('INFLUX_TOKEN') is not None:
    iftoken  = os.getenv('INFLUX_TOKEN')
elif os.path.exists(INFLUX_TOKEN_FILE):
    with open(INFLUX_TOKEN_FILE, 'r') as file:
        iftoken = file.read().strip()
else:    
    print('No InfluxDB Token found.')
    print('Please add the Token. Exiting now.')
    sys.exit(1)

# take a timestamp for this measurement
oldtime = str(sys.argv[6]) #30/May/2023:14:16:48 +0000 to 2009-11-10T23:00:00+00:00 (+00:00 is Timezone)
#transform month
month_map = {'Jan': '01', 'Feb': '02', 'Mar': '03', 'Apr': '04', 'May': '05', 'Jun': '06', 'Jul': '07', 'Aug': '08', 'Sep': '09', 'Oct': '10', 'Nov': '11', 'Dec': '12'}
month = month_map.get(oldtime[3:6], '12')
# build new time
time_str = f"{oldtime[7:11]}-{month}-{oldtime[0:2]}T{oldtime[12:20]}{oldtime[21:24]}:{oldtime[24:26]}"
print('Measurement Time: ', time_str)

ifclient = influxdb_client.InfluxDBClient(
    url=ifhost,
    token=iftoken,
    org=iforg
)

# write the measurement
write_api = ifclient.write_api(write_options=SYNCHRONOUS)

point = influxdb_client.Point(measurement_name)
point.tag("Domain", Domain)
point.tag("IP", IP),
point.tag("Target", Target)

point.field("Domain", Domain)
point.field("IP", IP)
point.field("Target", Target)
point.field("browser", browser)
point.field("browser_version", browser_version)
point.field("os", os_family)
point.field("length", length)
point.field("statuscode", statuscode)
point.field("metric", 1)

point.time(time_str)

write_api.write(bucket=ifbucket, org=iforg, record=point)

ifclient.close()

print ('*************** data send ******************')
