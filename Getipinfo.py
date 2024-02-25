#!/usr/bin/python3

import sys
import os
print ('**************** start *********************')
measurement_name = (sys.argv[5]) # get measurement from argv
print ('Measurement-name: '+measurement_name) 

# argv1 = outsideip, agrv2 = Domain, argv3 length, argv4 tragetip, sys.argv[5] bucketname, sys.argv[6] date, sys.argv[7] asn, sys.argv[8] abuse




abuseip_key = os.getenv('ABUSEIP_KEY')
if abuseip_key is not None:
    import requests
    import json
    url = 'https://api.abuseipdb.com/api/v2/check'
    querystring = {
        'ipAddress': str(sys.argv[1]),
        'maxAgeInDays': '90'
    }
    headers = {
        'Accept': 'application/json',
        'Key': abuseip_key
    }

    response = requests.request(method='GET', url=url, headers=headers, params=querystring)
    abuseip_response = json.loads(response.text)
    abuseConfidenceScore = str(abuseip_response["data"]["abuseConfidenceScore"])
    totalReports = str(abuseip_response["data"]["totalReports"])
    #print(json.dumps(abuseip_response, sort_keys=True, indent=4))


asn = str(sys.argv[7])

import geoip2.database
import socket 
 
# IP gets infos from the DB
reader = geoip2.database.Reader('/geolite/GeoLite2-City.mmdb')
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
reader.close()

if asn =='true':
    reader = geoip2.database.Reader('/geolite/GeoLite2-ASN.mmdb')
    response = reader.asn(str(sys.argv[1]))
    Asn = response.autonomous_system_organization
    reader.close()

# print to log
print (Country)
print (State)
print (City)
print (Zip)
print (Long)
print (Lat)
print (ISO)
if asn =='true':
    print (Asn)
print ('Outside IP: ', IP)
print ('Target IP: ', Target)
print ('Domain: ', Domain)
if abuseip_key is not None:
    print("abuseConfidenceScore: " + abuseConfidenceScore)
    print("totalReports: " + totalReports)

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS


# influx configuration - edit these
npmhome = "/root/.config/NPMGRAF"
ifhost = os.getenv('INFLUX_HOST')
ifbucket = os.getenv('INFLUX_BUCKET')
iforg    = os.getenv('INFLUX_ORG')
iftoken  = os.getenv('INFLUX_TOKEN')

# take a timestamp for this measurement
oldtime = str(sys.argv[6]) #30/May/2023:14:16:48 +0000 to 2009-11-10T23:00:00.123456Z
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
point.tag("key", ISO)
point.tag("latitude", Lat)
point.tag("longitude", Long)
point.tag("Domain", Domain)
point.tag("City", City)
point.tag("State", State)
point.tag("Name", Country)
point.tag("IP", IP),
point.tag("Target", Target)
if asn =='true':
    point.tag("Asn", Asn)
if abuseip_key is not None:
    point.tag("abuseConfidenceScore", abuseConfidenceScore)
    point.tag("totalReports", totalReports)

point.field("Domain", Domain)
point.field("latitude", Lat)
point.field("longitude", Long)
point.field("State", State)
point.field("City", City)
point.field("key", ISO)
point.field("IP", IP)
point.field("Target", Target)
if asn =='true':
    point.field("Asn", Asn)
point.field("Name", Country)
point.field("duration", duration)
point.field("metric", 1)
if abuseip_key is not None:
    point.field("abuseConfidenceScore", abuseConfidenceScore)
    point.field("totalReports", totalReports)

point.time(time)

write_api.write(bucket=ifbucket, org=iforg, record=point)

ifclient.close()

print ('*************** data send ******************')
