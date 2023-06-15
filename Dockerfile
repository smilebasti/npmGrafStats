FROM python:3

LABEL maintainer="npmgrafstats@wieser.myhome-server.de"

## setup home folder
RUN mkdir -p /root/.config/NPMGRAF

COPY requirements.txt /root/.config/NPMGRAF/requirements.txt
RUN pip install -r /root/.config/NPMGRAF/requirements.txt

## Copy files
COPY Getipinfo.py /root/.config/NPMGRAF/Getipinfo.py
RUN chmod +x  /root/.config/NPMGRAF/Getipinfo.py

COPY Internalipinfo.py /root/.config/NPMGRAF/Internalipinfo.py
RUN chmod +x  /root/.config/NPMGRAF/Internalipinfo.py

COPY sendips.sh /root/.config/NPMGRAF/sendips.sh
RUN chmod +x  /root/.config/NPMGRAF/sendips.sh

COPY sendredirectionips.sh /root/.config/NPMGRAF/sendredirectionips.sh
RUN chmod +x  /root/.config/NPMGRAF/sendredirectionips.sh

COPY start.sh /root/start.sh
RUN chmod +x  /root/start.sh

ENTRYPOINT ["/root/start.sh"]



