-e #!/bin/bash

# Build Docker images
docker build -t command-service:latest ./command_service
docker build -t websocket-listener-service:latest ./websocket_listener_service
docker build -t proxy-service:latest ./proxy_service

# Run Docker containers
docker run -d --name command-service -p 8000:8000 command-service:latest
docker run -d --name websocket-listener-service -p 8001:8000 websocket-listener-service:latest
docker run -d --name proxy-service -p 8002:8000 proxy-service:latest
