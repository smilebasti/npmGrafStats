# Stage 1: Build environment
FROM python:3.14-slim AS builder

LABEL maintainer="npmgrafstats@smilebasti.de"

# Setup home folder
RUN mkdir -p /home/appuser/.config/NPMGRAF

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
COPY requirements.txt /home/appuser/.config/NPMGRAF/requirements.txt
RUN pip install --no-cache-dir -r /home/appuser/.config/NPMGRAF/requirements.txt

# Stage 2: Runtime environment
FROM python:3.14-slim

# Setup home folder
RUN mkdir -p /home/appuser/.config/NPMGRAF

# Install curl in the final image
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN useradd --create-home --shell /bin/bash appuser

# Create /data directory and set ownership to appuser
RUN mkdir -p /data && chown -R appuser:appuser /data

# Copy the installed grepcidr binary from the builder stage
COPY --from=builder /usr/local/bin/grepcidr /usr/local/bin/grepcidr

# Copy installed Python packages from the builder stage
COPY --from=builder /usr/local/lib/python3.14/site-packages /usr/local/lib/python3.14/site-packages

# Copy Python scripts and set permissions
COPY Getipinfo.py /home/appuser/.config/NPMGRAF/Getipinfo.py
COPY Internalipinfo.py /home/appuser/.config/NPMGRAF/Internalipinfo.py
COPY sendips.sh /home/appuser/.config/NPMGRAF/sendips.sh
COPY start.sh /home/appuser/start.sh

RUN chmod +x /home/appuser/.config/NPMGRAF/*.py /home/appuser/start.sh

# Change ownership to non-root user
RUN chown -R appuser:appuser /home/appuser/.config/NPMGRAF /home/appuser/start.sh

# Switch to non-root user
USER appuser

# Set the entry point
ENTRYPOINT ["/home/appuser/start.sh"]
