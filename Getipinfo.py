#!/usr/bin/python3

import sys
# import geoip2.webservice
print ('**************** start *********************')
measurement_name = ("ReverseProxyConnections")
print (measurement_name) #prints Reverse Connections

# argv1 = outsideip, agrv2 = Domain, argv3 length, argv4 tragetip
print ('Ip: ', sys.argv[1])

# Hier wird dazwischen noch die Ziel IP-Adresse aufgelistet mit \n getrennt # geändert in sendips zu outside und Target

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

# Ausgabe
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
from influxdb import InfluxDBClient

## get env vars and use

import os
# influx configuration - edit these

npmhome = "/root/.config/NPMGRAF"
npmhome = os.getenv('NPMGRAF_HOME')
ifuser = os.getenv('INFLUX_USER')
ifpass = os.getenv('INFLUX_PW')
ifdb   = os.getenv('INFLUX_DB')
ifhost = os.getenv('INFLUX_HOST')
ifport = os.getenv('INFLUX_PORT')


print ('****************** end *******************')
# take a timestamp for this measurement
time = datetime.datetime.utcnow()

# format the data as a single measurement for influx
body = [
    {
        "measurement": measurement_name,
        "time": time,
        "tags": {
            "key": ISO,
            "latitude": Lat,
            "longitude": Long,
            "Domain": Domain,
            "City": City,
            "State": State,
            "name": Country,
            "IP": IP,
            "Target": Target
            },
        "fields": {
            "Domain": Domain,
            "latitude": Lat,
            "longitude": Long,
            "State": State,
            "City": City,
            "key": ISO,
            "IP": IP,
            "Target": Target,
            "name": Country,
            "duration": duration,
            "metric": 1
        }
    }
]

# connect to influx
ifclient = InfluxDBClient(ifhost,ifport,ifuser,ifpass,ifdb)

# write the measurement
ifclient.write_points(body)

