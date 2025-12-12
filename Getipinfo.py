#!/usr/bin/python3

import sys
import os
import geoip2.database
import socket
import json
import time
import fcntl
from datetime import datetime, timedelta
import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

print ('**************** start plus *********************')
measurement_name = (sys.argv[4]) # get measurement from argv
print ('Measurement-name: '+measurement_name) 

# argv[1[] = outsideip, agrv[2] = Domain, argv[3] length,  sys.argv[4] bucketname, sys.argv[5] date, sys.argv[6] asn, sys.argv[7] statuscode

# Configuration for Persistent Data
DATA_DIR = "/data"
CACHE_FILE = os.path.join(DATA_DIR, "abuseip_cache.json")
CACHE_EXPIRATION_HOURS = 48
INFLUX_TOKEN_FILE = os.path.join(DATA_DIR, "influxdb-token.txt")
ABUSEIP_KEY_FILE = os.path.join(DATA_DIR, "abuseipdb-key.txt")

# Abuseipdb cache
# Ensure the data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Function to load the cache from the file
def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)  # Shared lock: allows multiple readers
            data = json.load(f)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
            return data
    except (json.JSONDecodeError, IOError, OSError) as e:
        print(f"Error loading cache: {e}")
        return {}

# Function to save the cache to the file
def save_cache(cache_data):
    try:
        with open(CACHE_FILE, 'w') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock: blocks all other access
            json.dump(cache_data, f, indent=4)
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)  # Unlock
    except (IOError, OSError) as e:
        print(f"Error saving cache: {e}")

# Function to get AbuseIPDB info, using the cache
def get_abuseip_info(ip_address):
    cache = load_cache()
    current_time = time.time()

    # Check if a valid, non-expired entry exists in the cache
    if ip_address in cache:
        entry = cache[ip_address]
        entry_time = entry.get('timestamp', 0)
        if current_time - entry_time < CACHE_EXPIRATION_HOURS * 3600:
            print(f"Cache HIT for IP: {ip_address}")
            return entry['data']

    # If not in cache or expired, fetch from API (Cache MISS)
    print(f"Cache MISS for IP: {ip_address}. Fetching from API.")
    if os.path.exists(ABUSEIP_KEY_FILE):
        with open(ABUSEIP_KEY_FILE, 'r') as file:
            abuseip_key = file.read().strip()
    elif os.getenv('ABUSEIP_KEY') is not None:
        abuseip_key  = os.getenv('ABUSEIP_KEY')
    else:
        return None

    try:
        import requests
        url = 'https://api.abuseipdb.com/api/v2/check'
        querystring = {'ipAddress': ip_address, 'maxAgeInDays': '90'}
        headers = {'Accept': 'application/json', 'Key': abuseip_key}

        response = requests.request(method='GET', url=url, headers=headers, params=querystring)
        response.raise_for_status() # Will raise an exception for HTTP error codes

        api_data = response.json().get("data")
        if api_data:
            # Update cache with new data and timestamp
            cache[ip_address] = {'timestamp': current_time, 'data': api_data}
            save_cache(cache)
        return api_data
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return None
    except json.JSONDecodeError:
        print("Failed to parse API response.")
        return None

abuseConfidenceScore = "0"
totalReports = "0"
abuseip_key = None

if os.path.exists(ABUSEIP_KEY_FILE):
    with open(ABUSEIP_KEY_FILE, 'r') as file:
        abuseip_key = file.read().strip()
elif os.getenv('ABUSEIP_KEY') is not None:
    abuseip_key  = os.getenv('ABUSEIP_KEY')
    
if abuseip_key:
    abuseip_data = get_abuseip_info(sys.argv[1])
    if abuseip_data:
        abuseConfidenceScore = str(abuseip_data.get("abuseConfidenceScore", "0"))
        totalReports = str(abuseip_data.get("totalReports", "0"))
 
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
length = int(sys.argv[3])
statuscode = int(sys.argv[7])
reader.close()

asn = str(sys.argv[6])
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
print ('Domain: ', Domain)
print ('Statuscode ', statuscode)
if abuseip_key:
    print("abuseConfidenceScore: " + abuseConfidenceScore)
    print("totalReports: " + totalReports)

# influx configuration - edit these
npmhome = "/root/.config/NPMGRAF"
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
oldtime = str(sys.argv[5]) #30/May/2023:14:16:48 +0000 to 2009-11-10T23:00:00.123456Z
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
point.tag("key", ISO)
point.tag("latitude", Lat)
point.tag("longitude", Long)
point.tag("Domain", Domain)
point.tag("City", City)
point.tag("State", State)
point.tag("Name", Country)
point.tag("IP", IP)
if asn =='true':
    point.tag("Asn", Asn)
if abuseip_key:
    point.tag("abuseConfidenceScore", abuseConfidenceScore)
    point.tag("totalReports", totalReports)

point.field("Domain", Domain)
point.field("latitude", Lat)
point.field("longitude", Long)
point.field("State", State)
point.field("City", City)
point.field("key", ISO)
point.field("IP", IP)
if asn =='true':
    point.field("Asn", Asn)
point.field("Name", Country)
point.field("length", length)
point.field("statuscode", statuscode)
point.field("metric", 1)
if abuseip_key:
    point.field("abuseConfidenceScore", abuseConfidenceScore)
    point.field("totalReports", totalReports)

point.time(time_str)

write_api.write(bucket=ifbucket, org=iforg, record=point)

ifclient.close()

print ('*************** plus data send ******************')
