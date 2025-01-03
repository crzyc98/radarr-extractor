# First stage: Install dependencies
FROM python:3.9-slim-bullseye AS builder
WORKDIR /app
RUN echo "deb http://deb.debian.org/debian bullseye main contrib non-free" >> /etc/apt/sources.list && \
    apt-get update && \
    apt-get install -y unrar
# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && pip list
# Copy the application code
COPY . .

# Final stage: Create the runtime image
FROM python:3.9-slim-bullseye
WORKDIR /app
# Copy the app from the builder
COPY --from=builder /app /app
# Copy the unrar executable from the builder
COPY --from=builder /usr/bin/unrar /usr/bin/unrar
# Copy the installed packages from the builder
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
# Create a non-root user and set permissions
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app \
    && mkdir -p /downloads /downloads/extracted \
    && chown -R appuser:appuser /downloads /downloads/extracted
USER appuser
# Expose Flask port (if needed)
EXPOSE 5000
# Health check to ensure container is running
HEALTHCHECK --interval=5m --timeout=3s \
    CMD python -c 'import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(("127.0.0.1", 5000)); s.close();'
# Default command
CMD ["python", "-m", "radarr_extractor.main"]