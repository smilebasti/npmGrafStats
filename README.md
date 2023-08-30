# npmGrafStats
NginxProxyManager Grafana Statistics.

This project analyzes the logs of the Nginx Proxy Manager and exports them to InfluxDB to be used in a Grafana Dashboard.

npmGrafStats can save the Revers-Proxy and/or the Redirection Logs. Also a exclusion of IP's from for example external montitoring services is possible. 

### Following Data is extracted from the Logs:
- source IP
- target IP in your home network set in NPM
- the targeted domain
- the measurement time
- the Data of the source IP from GeoLite2-City.mmdb
  - Country
  - Coordinates
  - City

A view of the Grafana Dashboard only within a few hours of running:
![npmGrafStats](https://user-images.githubusercontent.com/60941345/203383131-50b7197e-2e58-4bb1-a7e6-d92e15d3430a.png)

## Newest features
v2.3.2 added in the Grafana dashboard a filter option to select only a few specific domains. Also the latest image is now running python:3-slim as base image (***80% smaller*** than before!).

This project is a modified clone of  https://github.com/Festeazy/nginxproxymanagerGraf and independent of https://github.com/jc21/nginx-proxy-manager. Changes to the original project can be found in the [changelog.md](https://github.com/smilebasti/npmGrafStats/blob/main/changelog.md) file.


### Obviously I'd appreciate anyhelp or feedback :) Hope you enjoy. If you do so, please star this project.

# Installation
If you are only able to use InfluxDB v1 see Branch: https://github.com/smilebasti/npmGrafStats/tree/influx-v1. This Branch is not being developed anymore!

### The Installation instructions can now be found in the [GitHub Wiki](https://github.com/smilebasti/npmGrafStats/wiki). 
Currently supported architectures: `amd64`, `arm/v7` and `arm64`.

Github Registry is now additionally available to Docker Registry by adding `ghcr.io/` in front of `smilebasti/npmgrafstats:latest`.

A full installation example is available with the [docker-compose.yml](https://github.com/smilebasti/npmGrafStats/blob/main/docker-compose.yml)

