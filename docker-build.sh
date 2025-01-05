docker build --platform linux/amd64 -t crzyc/radarr-extractor:latest .
docker login
docker push crzyc/radarr-extractor:latest