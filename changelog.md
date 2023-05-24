# Changelog

### Todo list
- use logtime and not hosttime to save the stats
- Stop gathering after few days

## v2.1.1
- fix redirection logs
- added Redirections and ReverseProxy Dashboard to Grafana
- fix Readme.md
- New Grafana ID 18826 (i accidentally the old one. Sorry)

## v2.1.0
- clean up Dockerfile
- print and set measurment name
- print 'data send' after influx send
- added sendredirectionips.sh for redirection logs
- true statement for redirection logs
- removed NPMGRAF_HOME variable
- changed docker naming sheme to version number
- added internal-ip filter
- changed from sh to bash to use regex

## v2.0.0
### Dev info/changes made to original
To the Original Project following changes were made:
- the new log format and only the proxy-host*-access.log from NPM are used
- Domains now allow a "-" in the domain
- no subdomains or subdomains up to 3 levels extra (sub.sub.sub.domain.tld)
- the targeted internal ip is logged
- using influxdb v2

#### Detailed
- args parssed sendips.sh to Getipinfo.py: 1. Outside IP 2. Domain 3. length 4. Target IP
- These Domain only registered for me : .env.de, config.php.com(.de,.org)
- Add Domains to Dashboard
- Did NPM change the log format? -> to access.log
- exclude external Ip
- add apk grep for --line-buffered as not included in bash in busybox -> overflow -> process stopped
- upgrade to influx 2 - see project https://github.com/evijayan2/nginxproxymanagerGraf

