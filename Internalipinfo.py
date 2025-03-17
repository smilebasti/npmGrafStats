#!/usr/bin/python3

import sys
print ('**************** start *********************')
measurement_name = (sys.argv[5]) # get measurement from argv
print ('Measurement-name: '+measurement_name) 

# argv1 = outsideip, agrv2 = Domain, argv3 length, argv4 tragetip

import socket 
 
IP = str(sys.argv[1])
Domain = str(sys.argv[2])
duration = int(sys.argv[3])
Target = str(sys.argv[4])

# print to log
print ('Calling IP: ', IP)
print ('Target IP: ', Target)
print ('Domain: ', Domain)

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

## get env vars and use
import os
# influx configuration - edit these

npmhome = "/root/.config/NPMGRAF"
ifhost = os.getenv('INFLUX_HOST')
ifbucket = os.getenv('INFLUX_BUCKET')
iforg    = os.getenv('INFLUX_ORG')
iftoken  = os.getenv('INFLUX_TOKEN')
iftokenfile = os.getenv('INFLUX_TOKEN_FILE')
if iftokenfile is not None and os.path.isfile(iftokenfile):
    with open(iftokenfile, 'r') as file:
        iftoken = file.read().strip()

# take a timestamp for this measurement
oldtime = str(sys.argv[6]) #30/May/2023:14:16:48 +0000 to 2009-11-10T23:00:00+00:00 (+00:00 is Timezone)
#transform month
month = oldtime[3:6]
if month == 'Jan':
    month = '01'
elif month =='Feb':
    month = '02'
elif month =='Mar':
    month = '03'
elif month =='Apr':
    month = '04'
elif month =='May':
    month = '05'
elif month =='Jun':
    month = '06'
elif month =='Jul':
    month = '07'
elif month =='Aug':
    month = '08'
elif month =='Sep':
    month = '09'
elif month =='Oct':
    month = '10'
elif month =='Nov':
    month = '11'
else:
    month = '12'

# build new time
time=oldtime[7:11]+'-'+month+'-'+oldtime[0:2]+'T'+oldtime[12:20]+oldtime[21:24]+':'+oldtime[24:26]
print('Measurement Time: ', time)

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
point.field("duration", duration)
point.field("metric", 1)

point.time(time)

write_api.write(bucket=ifbucket, org=iforg, record=point)

ifclient.close()

print ('*************** data send ******************')
