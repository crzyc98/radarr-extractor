ARG TARGETPLATFORM
FROM --platform=$TARGETPLATFORM python:3.9-slim-bullseye as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

FROM --platform=$TARGETPLATFORM python:3.9-slim-bullseye

WORKDIR /app
COPY --from=builder /app /app

RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=5m --timeout=3s \
  CMD python -c 'import socket; s = socket.socket(socket.AF_INET, socket.SOCK_STREAM); s.connect(("127.0.0.1", 5000)); s.close();'

CMD ["python", "-m", "radarr_extractor.main"]