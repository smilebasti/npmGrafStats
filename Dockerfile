FROM python:3.14-slim

LABEL maintainer="npmgrafstats@smilebasti.de"

RUN useradd --create-home --shell /bin/bash appuser && \
    mkdir -p /data /home/appuser/app && \
    chown -R appuser:appuser /data /home/appuser/app

COPY src/requirements.txt /home/appuser/app/requirements.txt
RUN pip install --no-cache-dir -r /home/appuser/app/requirements.txt

COPY src/ /home/appuser/app/
RUN chown -R appuser:appuser /home/appuser/app

USER appuser
WORKDIR /home/appuser/app

ENTRYPOINT ["python", "-u", "main.py"]
