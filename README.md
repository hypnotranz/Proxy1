# Proxy Services

This project includes multiple services managed with Docker Compose.

## Setup

1. Ensure Docker and Docker Compose are installed.
2. Clone the repository.
3. Navigate to the project root directory.

```sh
 git clone <repository_url>
 cd Proxy_Services
```

## Running the Services

To build and start all services, run:

```sh
 docker-compose up --build
```

```sh
 docker-compose up 
```


## Services

- **Proxy Service**: Runs on port 8080.
- **WebSocket Listener Service**: Runs on port 8002.
- **Command Service**: Runs on port 8001.
- **Elasticsearch**: Runs on port 9200.

## Stopping the Services

To stop all services, run:

```sh
 docker-compose down
```

## Manually Running Services

If you prefer to run services manually without Docker Compose, follow these steps:

1. **Start Proxy Service**

```sh
 cd proxy_service
 python proxy.py
```

2. **Start WebSocket Listener Service**

```sh
 cd websocket_listener_service
 python -m websocket_listener_service.main
```

3. **Start Command Service**

```sh
 cd command_service
 python -m main
```
