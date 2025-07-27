# First stage: Install dependencies
FROM python:3.9-slim-bullseye AS builder
WORKDIR /app
RUN echo "deb http://deb.debian.org/debian bullseye main contrib non-free" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y unrar wget ca-certificates && \
    wget -O /usr/local/bin/gosu "https://github.com/tianon/gosu/releases/download/1.17/gosu-$(dpkg --print-architecture)" && \
    chmod +x /usr/local/bin/gosu && \
    gosu nobody true
# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip list
# Copy the application code
COPY . .

# Final stage: Create the runtime image
FROM python:3.9-slim-bullseye
WORKDIR /app

# Build arguments for user creation
ARG PUID=1000
ARG PGID=1000

# Copy the app from the builder
COPY --from=builder /app /app
# Copy the unrar executable from the builder
COPY --from=builder /usr/bin/unrar /usr/bin/unrar
# Copy gosu from the builder
COPY --from=builder /usr/local/bin/gosu /usr/local/bin/gosu
# Copy the installed packages from the builder
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/

# Copy entrypoint script
COPY docker/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

# Create matching group & user to satisfy any USER appuser directive
RUN groupadd -g ${PGID} appuser && \
    useradd -u ${PUID} -g appuser -M -s /usr/sbin/nologin appuser && \
    mkdir -p /downloads /downloads/extracted /config && \
    chown -R appuser:appuser /app /downloads /config

# NOTE: Don't set USER here - entrypoint will handle user switching

# Expose Flask port (configurable via WEBHOOK_PORT, defaults to 9898)
EXPOSE 9898

# Health check temporarily removed for debugging

# Set entrypoint and default command
ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["python", "-m", "radarr_extractor.main"]