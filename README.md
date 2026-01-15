# npmPlusGrafStats
NginxProxyManagerPlus Grafana Statistics.

This project analyzes the logs of the Nginx Proxy Manager Plus and exports them to InfluxDB to be used in a Grafana Dashboard. npmPlusGrafStats can save the Revers-Proxy and/or the Redirection Logs. Also a exclusion of IP's from for example external montitoring services is possible. 

### npm and **not** npmPlus
If you are **not** using npmPlus have a look at the branch: [main](https://github.com/smilebasti/npmGrafStats)

### Following Data is extracted from the Logs:
- source IP
- target IP in your home network set in NPM
- the targeted domain
- the measurement time
- the status code
- the bytes transported
- the Browser and OS
- the Data of the source IP from GeoLite2-City.mmdb
  - Country
  - Coordinates
  - City

A view of the Grafana Dashboard only within a few hours of running:
![npmGrafStats](https://user-images.githubusercontent.com/60941345/203383131-50b7197e-2e58-4bb1-a7e6-d92e15d3430a.png)

## Newest features
v3.1.0 adds Browser and OS to the Dashboard. Also Fixes Grafana ID: With Filter 18826 and No Filter 24693

This project is a modified clone of  https://github.com/Festeazy/nginxproxymanagerGraf and independent of https://github.com/jc21/nginx-proxy-manager and https://github.com/ZoeyVid/NPMplus. Changes to the original project can be found in the [changelog.md](https://github.com/smilebasti/npmGrafStats/blob/npmPlus-main/changelog.md) file.

### Obviously I'd appreciate any help or feedback :) Hope you enjoy. If you do so, please star this project.

# Installation
The Installation instructions can be found in the [GitHub Wiki](https://github.com/smilebasti/npmGrafStats/wiki). 
A full setup example is available with the [docker-compose.yml](https://github.com/smilebasti/npmGrafStats/blob/npmPlus-main/docker-compose.yml)

Currently supported architectures: `amd64`, `arm/v7` and `arm64`.

Github Registry is additionally available to Docker Registry by adding `ghcr.io/` in front of `smilebasti/npmgrafstats:latest`.

## Star History

[![Star History Chart](https://api.star-history.com/svg?repos=smilebasti/npmgrafstats&type=Date)](https://star-history.com/#smilebasti/npmgrafstats&Date)