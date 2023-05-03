# npmGrafStats
NginxProxyManager Grafana Statistic.

This project analyzes the logs of the Nginx Proxy Manager and exports it to InfluxDB to be used in a Grafana Dashboard.

It saves following Data:
- source IP
- target IP in your home network set in NPM
- the targeted domain
- the Data of the source IP from GeoLite2-City.mmdb
  - Country
  - Coordinates
  - City

![npmGrafStats](https://user-images.githubusercontent.com/60941345/203383131-50b7197e-2e58-4bb1-a7e6-d92e15d3430a.png)

This project is a modified clone of  https://github.com/Festeazy/nginxproxymanagerGraf and independent of https://github.com/jc21/nginx-proxy-manager.

If you are using InfluxDB v1 see Branch: https://github.com/smilebasti/npmGrafStats/tree/influx-v1

## required things for the installation

1) create an influx Organisation called npmgrafstats
2) Create a Bucket called npmgrafstatsand a API-Tocken for npmgrafstats
3) Set HOME_IPS to your External/Public IP (if multiple external IP Addresses separated them with \| )
4) get your GeoLite2-City.mmdb from the geoliteupdate container (docker-compose file below) or download it to the working directory manually
5) Start the docker container or docker compose with ajusted settings
6) Add data source into grafana
7) Import the dashboard file or download it with the ID:  and set the new data source (Nginx Proxy Manager.json)

## start docker on the same host where nginx proxy manger runs
- Follwoing the working directory is /home/docker !
- NPM's docker-compose file and data directory are under /home/docker/nginx-proxy-manager !
- GeoLite2-City.mmdb is in /home/data
### Docker command
```
docker run --name npmgraf -it -d
-v /home/docker/nginx-proxy-manager/data/logs:/logs \
-v /home/docker/GeoLite2-City.mmdb:/GeoLite2-City.mmdb \
-e HOME_IPS=external IP \
-e INFLUX_HOST=192.168.0.189:8086 \
-e INFLUX_BUCKET=npmgrafstats \
-e INFLUX_ORG=npmgrafstats \
-e INFLUX_TOKEN=<replace> \
smilebasti/npmgrafstats
```
### Docker Compose file
```
version: '3'
services:
  npmgraf:
    image: smilebasti/npmgrafstats
    environment:
      - HOME_IPS=extrenal IP
      - INFLUX_HOST=192.168.0.189:8086
      - INFLUX_BUCKET=npmgrafstats
      - INFLUX_ORG=npmgrafstats
      - INFLUX_TOKEN=<replace>
    volumes:
      - /home/docker/nginx-proxy-manager/data/logs:/logs
      - /home/docker/GeoLite2-City.mmdb:/GeoLite2-City.mmdb
```

## GeoLite2-City.mmdb Auto update
Use this Docker Compose file to automaticly update the GeoLite2-City.mmdb
Set your ID and Key!
```
version: '3'
services:
  geoipupdate:
    image: maxmindinc/geoipupdate
    environment:
      - GEOIPUPDATE_ACCOUNT_ID=<replace>
      - GEOIPUPDATE_LICENSE_KEY=<replace>
      - GEOIPUPDATE_EDITION_IDS=GeoLite2-City
      - GEOIPUPDATE_FREQUENCY=24
    volumes:
      - /home/docker:/usr/share/GeoIP
```

## Grafana world map
Import Npm-Map-Dashboard-influxv2.json file to grafana (or use the Grafana Dashboard-ID: #18360) 
https://grafana.com/grafana/dashboards/18360-npm-map-influx-v2/

Obviously I'd appreciate help or any feedback :) 
Hope you enjoy

## Dev info/changes made to original
To the Original Project following changes were made:
- the new log format and only the proxy-host*-access.log from NPM are used
- Domains now allow a - in the domain
- no subdomains or subdomains up to 3 levels extra (sub.sub.sub.domain.tld)
- the targeted internal ip is loged
- using influxdb v2

### Detailed
- args parssed sendips.sh to Getipinfo.py: 1. Outside IP 2. Domain 3. length 4. Target IP
- These Domain only registered for me : .env.de, config.php.com(.de,.org)
- Add Domains to Dashboard
- Did NPM change the log format? -> to access.log
- exclude external Ip
- add apk grep for --line-buffered as not included in bash in busybox -> overflow -> process stopped
- upgrade to influx 2 - see project https://github.com/evijayan2/nginxproxymanagerGraf

### Todo list
- use logtime and not hosttime to save the stats
