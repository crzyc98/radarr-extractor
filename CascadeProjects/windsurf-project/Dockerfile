FROM python:3.9-slim

# Add non-free repository and install system dependencies
RUN echo "deb http://deb.debian.org/debian bookworm non-free" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y \
    unrar-free \
    unzip \
    p7zip-full \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the script
COPY radarr_extractor.py .

# Run the script
CMD ["python", "radarr_extractor.py"]
