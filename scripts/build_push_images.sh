#!/bin/bash

# Set your Docker Hub username
DOCKER_HUB_USERNAME="your_dockerhub_username"

# Build Docker images
docker build -t $DOCKER_HUB_USERNAME/command-service:latest ./command_service
docker build -t $DOCKER_HUB_USERNAME/websocket-listener-service:latest ./websocket_listener_service
docker build -t $DOCKER_HUB_USERNAME/proxy-service:latest ./proxy_service

# Push Docker images to Docker Hub
docker push $DOCKER_HUB_USERNAME/command-service:latest
docker push $DOCKER_HUB_USERNAME/websocket-listener-service:latest
docker push $DOCKER_HUB_USERNAME/proxy-service:latest
