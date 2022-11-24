#!/usr/bin/python3

import sys
# import geoip2.webservice
print ('**************** start *********************')
measurement_name = ("ReverseProxyConnections")
print (measurement_name) #prints Reverse Connections

# argv1 = outsideip, agrv2 = Domain, argv3 length, argv4 tragetip
print ('Ip: ', sys.argv[1])

import geoip2.database
import socket 

# IP gets infos from the DB
reader = geoip2.database.Reader('/GeoLite2-City.mmdb')
response = reader.city(str(sys.argv[1]))

Lat = response.location.latitude
ISO = response.country.iso_code
Long = response.location.longitude
State = response.subdivisions.most_specific.name
City = response.city.name
Country = response.country.name
Zip = response.postal.code
IP = str(sys.argv[1])
Domain = str(sys.argv[2])
duration = int(sys.argv[3])
Target = str(sys.argv[4])

# print to log
print (Country)
print (State)
print (City)
print (Zip)
print (Long)
print (Lat)
print (ISO)
print ('Outside IP: ', IP)
print ('Target IP: ', Target)
print ('Domain: ', Domain)
reader.close()


import datetime
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

## get env vars and use
import os
# influx configuration - edit these

npmhome = "/root/.config/NPMGRAF"
npmhome = os.getenv('NPMGRAF_HOME')
ifuser = os.getenv('INFLUX_USER')
ifpass = os.getenv('INFLUX_PW')
ifdb   = os.getenv('INFLUX_DB')
ifhost = os.getenv('INFLUX_HOST')
ifbucket = os.getenv('INFLUX_BUCKET')
iforg    = os.getenv('INFLUX_ORG')
iftoken  = os.getenv('INFLUX_TOKEN')


print ('****************** end *******************')
# take a timestamp for this measurement
time = datetime.datetime.utcnow()

ifclient = influxdb_client.InfluxDBClient(
    url=ifhost,
    token=iftoken,
    org=iforg
)

# write the measurement
write_api = ifclient.write_api(write_options=SYNCHRONOUS)

point = influxdb_client.Point(measurement_name)
point.tag("key", ISO)
point.tag("Latitude", Lat)
point.tag("Longitude", Long)
point.tag("Domain", Domain)
point.tag("City", City)
point.tag("State", State)
point.tag("Name", Country)
point.tag("IP", IP),
point.tag("Target", Target)

point.field("Domain", Domain)
point.field("Latitude", Lat)
point.field("Longitude", Long)
point.field("State", State)
point.field("City", City)
point.field("key", ISO)
point.field("IP", IP)
point.field("Target", Target)
point.field("Name", Country)
point.field("duration", duration)
point.field("metric", 1)

write_api.write(bucket=ifbucket, org=iforg, record=point)


