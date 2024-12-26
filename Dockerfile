# First stage: Install dependencies
FROM python:3.9-slim-bullseye AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y unrar
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
# Copy the installed packages from the builder
COPY --from=builder /usr/local/lib/python3.9/site-packages/ /usr/local/lib/python3.9/site-packages/
# Create a non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app
USER appuser
# Expose Flask port (if needed)
EXPOSE 5000
# Health check to ensure container is running
HEALTHCHECK --interval=5m --timeout=3s \
    CMD python -c 'import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(("127.0.0.1", 5000)); s.close();'
# Default command
CMD ["python", "-m", "radarr_extractor.main"]