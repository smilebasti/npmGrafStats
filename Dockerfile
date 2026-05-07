FROM python:3.14-slim

LABEL maintainer="npmgrafstats@smilebasti.de"

# NPMplus stores its access logs under /data/logs with mode 0700 owned by root.
# Reading them requires either matching that uid or running with directory-search
# rights, so the container runs as root by default. Override via the docker
# `user:` directive if you have a setup where logs are world-readable.

RUN mkdir -p /data /app

COPY src/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY src/ /app/
WORKDIR /app

ENTRYPOINT ["python", "-u", "main.py"]
