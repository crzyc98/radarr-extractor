# Use the official slim Python image for a smaller base image
FROM python:3.11-slim

# Set environment variables for better compatibility and predictable behavior
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /app

# Copy only the necessary files to the container
COPY requirements.txt /app/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . /app

# Specify the command to run your app
CMD ["python", "-m", "radarr_extractor.core"]