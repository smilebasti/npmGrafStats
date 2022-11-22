FROM alpine:latest

#add curl for better handling
RUN apk add --no-cache curl
RUN apk add linux-headers 
# Update & Install dependencies
RUN apk add --no-cache --update \
    git \
    bash \
    libffi-dev \
    openssl-dev \
    bzip2-dev \
    zlib-dev \
    readline-dev \
    sqlite-dev \
    build-base \
    grep

# Set Python version
ARG PYTHON_VERSION='3.7.15'
RUN export PYTHON_VERSION
# Set pyenv home
ARG PYENV_HOME=/root/.pyenv
RUN export PYENV_HOME

# Install pyenv, then install python versions
RUN git clone --depth 1 https://github.com/pyenv/pyenv.git $PYENV_HOME && \
    rm -rfv $PYENV_HOME/.git

ENV PATH $PYENV_HOME/shims:$PYENV_HOME/bin:$PATH

RUN pyenv install $PYTHON_VERSION
RUN pyenv global $PYTHON_VERSION
RUN pip install --upgrade pip && pyenv rehash
RUN pip install geoip2
RUN pip install influxdb

# Clean
RUN rm -rf ~/.cache/pip

# Done python3.7 setup

## setup home folder
RUN mkdir -p /root/.config/NPMGRAF

ENV NPMGRAF_HOME=/root/.config/NPMGRAF
ARG NPMGRAF_HOME=/root/.config/NPMGRAF
RUN export NPMGRAF_HOME

## Copy files
COPY Getipinfo.py /root/.config/NPMGRAF/Getipinfo.py
RUN chmod +x  /root/.config/NPMGRAF/Getipinfo.py

COPY sendips.sh /root/.config/NPMGRAF/sendips.sh
RUN chmod +x  /root/.config/NPMGRAF/sendips.sh

COPY start.sh /root/start.sh
RUN chmod +x  /root/start.sh

ENTRYPOINT ["/root/start.sh"]



