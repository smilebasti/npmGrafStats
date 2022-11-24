FROM python:3

## setup home folder
RUN mkdir -p /root/.config/NPMGRAF

ENV NPMGRAF_HOME=/root/.config/NPMGRAF
ARG NPMGRAF_HOME=/root/.config/NPMGRAF
RUN export NPMGRAF_HOME

## exludeHOMEIps
ENV HOME_IPS="192.168.0.*\|192.168.10.*"
ARG HOME_IPS="192.168.0.*\|192.168.10.*"


## seting up influx connection
ENV INFLUX_USER=admin
ARG INFLUX_USER=admin

ENV INFLUX_PW=admin
ARG INFLUX_PW=admin

ENV INFLUX_DB=DB
ARG INFLUX_DB=DB

ENV INFLUX_HOST=192.168.0.11
ARG INFLUX_HOST=192.168.0.11

ENV INFLUX_PORT=192.168.0.11
ARG INFLUX_PORT=192.168.0.11

ENV INFLUX_BUCKET=influxdb
ARG INFLUX_BUCKET=influxdb

ENV INFLUX_ORG=influxdb
ARG INFLUX_ORG=influxdb

ENV INFLUX_TOKEN=influxdb
ARG INFLUX_TOKEN=influxdb


COPY requirements.txt /root/.config/NPMGRAF/requirements.txt
RUN pip install -r /root/.config/NPMGRAF/requirements.txt

## Copy files
COPY Getipinfo.py /root/.config/NPMGRAF/Getipinfo.py
RUN chmod +x  /root/.config/NPMGRAF/Getipinfo.py

COPY sendips.sh /root/.config/NPMGRAF/sendips.sh
RUN chmod +x  /root/.config/NPMGRAF/sendips.sh

COPY start.sh /root/start.sh
RUN chmod +x  /root/start.sh

ENTRYPOINT ["/root/start.sh"]
