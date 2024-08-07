#!/bin/bash

# Apply Elasticsearch deployments
kubectl apply -f ./elasticsearch/command_service-elasticsearch.yaml
kubectl apply -f ./elasticsearch/websocket_listener_service-elasticsearch.yaml

# Apply service deployments
kubectl apply -f ./kubernetes/command_service-deployment.yaml
kubectl apply -f ./kubernetes/websocket_listener_service-deployment.yaml
kubectl apply -f ./kubernetes/proxy_service-deployment.yaml

# List all pods and services to verify
kubectl get pods
kubectl get services
