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
# Copy gosu from the builder (for potential runtime use)
COPY --from=builder /usr/local/bin/gosu /usr/local/bin/gosu
# Copy the installed packages from the builder
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/

# Create group and user with specified PUID/PGID
RUN groupadd -g ${PGID} appuser && \
    useradd -u ${PUID} -g appuser -M -s /usr/sbin/nologin appuser && \
    mkdir -p /downloads /downloads/extracted /downloads/.extracted_files /config && \
    chown -R appuser:appuser /app /downloads /config

# Switch to non-root user
USER appuser

# Expose Flask port
EXPOSE 9898

# Health check to ensure container is running
HEALTHCHECK --interval=5m --timeout=3s \
    CMD python -c 'import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(("127.0.0.1", 9898)); s.close();' || exit 1

# Start the application directly
CMD ["python", "-m", "radarr_extractor.main"]