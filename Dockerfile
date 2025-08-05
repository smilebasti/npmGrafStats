# Stage 1: Build environment
FROM python:3.13-slim AS builder

LABEL maintainer="npmgrafstats@smilebasti.myhome-server.de"

# Setup home folder
RUN mkdir -p /root/.config/NPMGRAF

# Install necessary packages for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc git build-essential \
    && rm -rf /var/lib/apt/lists/*

# Clone, build, and install grepcidr
RUN git clone --depth 1 https://github.com/ryantig/grepcidr.git /opt/grepcidr && \
    cd /opt/grepcidr && \
    make && \
    make install && \
    rm -rf /opt/grepcidr

# Install Python packages
COPY requirements.txt /root/.config/NPMGRAF/requirements.txt
RUN pip install --no-cache-dir -r /root/.config/NPMGRAF/requirements.txt

# Stage 2: Runtime environment
FROM python:3.13-slim

# Setup home folder
RUN mkdir -p /root/.config/NPMGRAF

# Install curl in the final image
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy the installed grepcidr binary from the builder stage
COPY --from=builder /usr/local/bin/grepcidr /usr/local/bin/grepcidr

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages

# Copy Python scripts and set permissions
COPY Getipinfo.py /root/.config/NPMGRAF/Getipinfo.py
COPY Internalipinfo.py /root/.config/NPMGRAF/Internalipinfo.py
COPY sendips.sh /root/.config/NPMGRAF/sendips.sh
COPY sendredirectionips.sh /root/.config/NPMGRAF/sendredirectionips.sh
COPY start.sh /root/start.sh

RUN chmod +x /root/.config/NPMGRAF/*.py /root/start.sh

# Set the entry point
ENTRYPOINT ["/root/start.sh"]