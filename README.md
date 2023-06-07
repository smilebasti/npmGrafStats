# npmGrafStats
NginxProxyManager Grafana Statistics.

This project analyzes the logs of the Nginx Proxy Manager and exports it to InfluxDB to be used in a Grafana Dashboard.

npmGrafStats can save the Revers-Proxy and/or the Redirection Logs. Also a exclusion of IP's from external montitoring services is possible.
Following Data is extracted from the Logs:
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

This project is a modified clone of  https://github.com/Festeazy/nginxproxymanagerGraf and independent of https://github.com/jc21/nginx-proxy-manager. Changes to the original project can be found in the [changelog.md](https://github.com/smilebasti/npmGrafStats/blob/main/changelog.md) file.


Obviously I'd appreciate anyhelp or feedback :) 
Hope you enjoy

# Installation
If you are using InfluxDB v1 see Branch: https://github.com/smilebasti/npmGrafStats/tree/influx-v1. This Branch is not going to be developed in the future!

### The Installation instructions can now be found in the [GitHub Wiki](https://github.com/smilebasti/npmGrafStats/wiki). 
Currently supported architectures: amd64 (Arm in development)

A full installation example is availlable with the [docker-compose.yml](https://github.com/smilebasti/npmGrafStats/blob/main/docker-compose.yml)
