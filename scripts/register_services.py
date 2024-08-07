import requests

# Replace with the actual IPs of your deployed services
proxy_service_ip = "PROXY_SERVICE_IP"
command_service_ip = "COMMAND_SERVICE_IP"
websocket_listener_service_ip = "WEBSOCKET_LISTENER_SERVICE_IP"

# URLs for registration
register_url = f"http://{proxy_service_ip}:8000/register"

# Service data
services = [
    {
        "service_name": "command-service",
        "openapi_url": f"http://{command_service_ip}:8001/openapi.json"
    },
    {
        "service_name": "websocket-listener-service",
        "openapi_url": f"http://{websocket_listener_service_ip}:8002/openapi.json"
    }
]

# Register each service
for service_data in services:
    response = requests.post(register_url, json=service_data)
    print(f"Registering {service_data[service_name]}: {response.json()}")
