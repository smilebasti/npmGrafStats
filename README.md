# npmGrafStats
NginxProxyManager Grafana Statistics.

This project analyzes the logs of the Nginx Proxy Manager and exports it to InfluxDB to be used in a Grafana Dashboard.

It saves following Data from the Revers-Proxy and Redirection Logs:
- source IP
- target IP in your home network set in NPM
- the targeted domain
- the measurement time
- the Data of the source IP from GeoLite2-City.mmdb
  - Country
  - Coordinates
  - City

![npmGrafStats](https://user-images.githubusercontent.com/60941345/203383131-50b7197e-2e58-4bb1-a7e6-d92e15d3430a.png)

This project is a modified clone of  https://github.com/Festeazy/nginxproxymanagerGraf and independent of https://github.com/jc21/nginx-proxy-manager. Changes to the original project can be found in the changelog.md file.


Obviously I'd appreciate help or any feedback :) 
Hope you enjoy

# Installation
### If you are using InfluxDB v1 see Branch: https://github.com/smilebasti/npmGrafStats/tree/influx-v1. This Branch is not going to be developed in the future!
## required things for the installation

1) create an influx Organisation called npmgrafstats
2) Create a Bucket called npmgrafstats and a API-Token for npmgrafstats with write access
3) Set HOME_IPS to your External/Public IP
4) Set REDIRECTION_LOGS to TRUE for Reverse-Proxy and Redirection logs, to ONLY for only Redirection logs and FALSE for only Reverse-Proxy logs
5) create the monitoringips.txt file and fill it with the IP's of Uptimerobot, Hetrixtools or similar services. (1 IP per row)(This is optional but is recommended if you monitor your domains via http(s) with external services).
6) get your GeoLite2-City.mmdb from the geoliteupdate container (docker-compose file below) or download it to the /home/docker/geolite directory manually
7) Start the docker container or docker-compose with ajusted settings
8) Add InfluxDB Bucket npmgrafstats as data source into grafana
9) Download the dashboard file (NPM Map Dashboard v2.1.1.json) or import it with the ID: 18826 and set the new data source in Grafana

## start docker on the same host where nginx proxy manger runs
- In the following the working directory is /home/docker !
- NPM's docker-compose file and data directory are under /home/docker/nginx-proxy-manager !
- GeoLite2-City.mmdb is in /home/docker/geolite
### Docker command
```
docker run --name npmgraf -it -d
-v /home/docker/nginx-proxy-manager/data/logs:/logs \
-v /home/docker/geolite:/geolite \
-v /home/docker/monitoringips.txt:/monitoringips.txt \ # optional only mount if preexists and a wanted feature
-e HOME_IPS=<replace with external IP> \
-e INFLUX_HOST=<replace>:8086 \  # use host IP
-e INFLUX_BUCKET=npmgrafstats \
-e INFLUX_ORG=npmgrafstats \
-e INFLUX_TOKEN=<replace> \
-e REDIRECTION_LOGS=<set> # set to TRUE or FALSE or ONLY
smilebasti/npmgrafstats
```
### Docker Compose file
A complete docker-compose.yml file is availlibale with Npm, npmGrafStats, InfluxDB, GeoLite, Grafana and Portainer.
```
version: '3'
services:
  npmgraf:
    image: smilebasti/npmgrafstats
    environment:
      - HOME_IPS=<replace with external IP>
      - INFLUX_HOST=<replace>:8086  # use host IP
      - INFLUX_BUCKET=npmgrafstats
      - INFLUX_ORG=npmgrafstats
      - INFLUX_TOKEN=<replace>
      - REDIRECTION_LOGS=<set> # set to TRUE or FALSE or ONLY
    volumes:
      - /home/docker/nginx-proxy-manager/data/logs:/logs
      - /home/docker/geolite:/geolite
      - /home/docker/monitoringips.txt:/monitoringips.txt # optional only mount if preexists and a wanted feature
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
      - /home/docker/geolite:/usr/share/GeoIP
```

## Grafana world map
### The ID changed!! accidentally deleted the old one. Sorry.
Import NPM-Map-Dashboard-v2.1.1.json file to grafana (or use the Grafana Dashboard-ID: #18826) 
https://grafana.com/grafana/dashboards/18826


