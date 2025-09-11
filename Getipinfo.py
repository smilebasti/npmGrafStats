#!/usr/bin/python3

import sys
import os
import json
import time
from datetime import datetime, timedelta

print('**************** start *********************')
measurement_name = sys.argv[4]  # get measurement from argv
print('Measurement-name: ' + measurement_name)

# --- Cache Configuration ---
NPMGRAF_HOME = "/root/.config/NPMGRAF"
CACHE_FILE = os.path.join(NPMGRAF_HOME, "abuseip_cache.json")
CACHE_EXPIRATION_HOURS = 24
# --- End Cache Configuration ---

# Function to load the cache from the file
def load_cache():
    if not os.path.exists(CACHE_FILE):
        return {}
    try:
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

# Function to save the cache to the file
def save_cache(cache_data):
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache_data, f, indent=4)
    except IOError as e:
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
    abuseip_key = os.getenv('ABUSEIP_KEY')
    if not abuseip_key:
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

# --- Main script execution ---

abuseConfidenceScore = "0"
totalReports = "0"

abuseip_data = get_abuseip_info(sys.argv[1])
if abuseip_data:
    abuseConfidenceScore = str(abuseip_data.get("abuseConfidenceScore", "0"))
    totalReports = str(abuseip_data.get("totalReports", "0"))


asn = str(sys.argv[6])

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
reader.close()

if asn == 'true':
    reader = geoip2.database.Reader('/geolite/GeoLite2-ASN.mmdb')
    response = reader.asn(str(sys.argv[1]))
    Asn = response.autonomous_system_organization
    reader.close()

# print to log
print(Country)
print(State)
print(City)
print(Zip)
print(Long)
print(Lat)
print(ISO)
if asn == 'true':
    print(Asn)
print('Outside IP: ', IP)
print('Domain: ', Domain)
print("abuseConfidenceScore: " + abuseConfidenceScore)
print("totalReports: " + totalReports)

import influxdb_client
from influxdb_client.client.write_api import SYNCHRONOUS

# influx configuration - edit these
ifhost = os.getenv('INFLUX_HOST')
ifbucket = os.getenv('INFLUX_BUCKET')
iforg = os.getenv('INFLUX_ORG')
iftoken = os.getenv('INFLUX_TOKEN')

# take a timestamp for this measurement
oldtime = str(sys.argv[5])
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
if asn == 'true':
    point.tag("Asn", Asn)
point.tag("abuseConfidenceScore", abuseConfidenceScore)
point.tag("totalReports", totalReports)

point.field("Domain", Domain)
point.field("latitude", Lat)
point.field("longitude", Long)
point.field("State", State)
point.field("City", City)
point.field("key", ISO)
point.field("IP", IP)
if asn == 'true':
    point.field("Asn", Asn)
point.field("Name", Country)
point.field("duration", duration)
point.field("metric", 1)
point.field("abuseConfidenceScore", abuseConfidenceScore)
point.field("totalReports", totalReports)

point.time(time_str)

write_api.write(bucket=ifbucket, org=iforg, record=point)

ifclient.close()

print('*************** data send ******************')
