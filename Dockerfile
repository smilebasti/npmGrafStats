FROM python:3-slim

LABEL maintainer="npmgrafstats@smilebasti.myhome-server.de"

## setup home folder
RUN mkdir -p /root/.config/NPMGRAF

## install curl for slim image
RUN apt-get update && apt-get install -y \
    curl gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /root/.config/NPMGRAF/requirements.txt
RUN pip install -r /root/.config/NPMGRAF/requirements.txt

## Copy files
COPY Getipinfo.py /root/.config/NPMGRAF/Getipinfo.py
RUN chmod +x  /root/.config/NPMGRAF/Getipinfo.py

COPY Internalipinfo.py /root/.config/NPMGRAF/Internalipinfo.py
RUN chmod +x  /root/.config/NPMGRAF/Internalipinfo.py

COPY sendips.sh /root/.config/NPMGRAF/sendips.sh
RUN chmod +x  /root/.config/NPMGRAF/sendips.sh

COPY start.sh /root/start.sh
RUN chmod +x  /root/start.sh

ENTRYPOINT ["/root/start.sh"]



