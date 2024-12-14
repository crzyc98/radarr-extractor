# Use consistent casing and remove redundant platform arguments
FROM python:3.9-slim-bullseye AS builder

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Final stage
FROM python:3.9-slim-bullseye

WORKDIR /app

# Copy built application from the builder stage
COPY --from=builder /app /app

# Create a non-root user and adjust permissions
RUN groupadd -r appuser && useradd -r -g appuser appuser \
    && chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Add a health check for the application
HEALTHCHECK --interval=5m --timeout=3s \
  CMD python -c 'import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(("127.0.0.1", 5000)); s.close();'

# Default command to run the application
CMD ["python", "-m", "radarr_extractor.main"]