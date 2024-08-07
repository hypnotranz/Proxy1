import asyncio
import websockets
import json
import logging
import requests
import os
import uuid
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel, Field
from typing import Any, Optional
from contextlib import asynccontextmanager
from fastapi.openapi.utils import get_openapi
import yaml

logging.basicConfig(level=logging.DEBUG)
app = FastAPI()

service_registry = {}

PROXY_URL = "http://localhost:8080/register"
DEREGISTER_PROXY_URL = "http://localhost:8080/deregister"
CONFIG_FILE = "listener_config.json"

class Envelope(BaseModel):
    endpoint_service_name: str = Field(..., description="Name of the service to forward the request to")
    endpoint_request_type: str = Field(..., description="HTTP method of the request (GET, POST, etc.)")
    endpoint_headers: Any = Field(default={}, description="Headers to include in the forwarded request")
    endpoint_params: Any = Field(default={}, description="Query parameters to include in the forwarded request")
    endpoint_body: Any = Field(default={}, description="Body of the forwarded request")
    connection_id: Optional[str] = Field(None, description="Connection ID for WebSocket listener")
    endpoint_url: str = Field(..., description="URL of the service to register")

class RegisterRequest(BaseModel):
    service_name: str
    url: str

class DeregisterRequest(BaseModel):
    service_name: str

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as file:
            logging.info("Loading configuration from file")
            return json.load(file)
    return {}

def save_config(config):
    with open(CONFIG_FILE, "w") as file:
        json.dump(config, file)

def get_connection_id():
    config = load_config()
    if "connection_id" not in config:
        config["connection_id"] = str(uuid.uuid4())
        save_config(config)
    return config["connection_id"]

# Get the connection ID (generate if it doesn't exist)
connection_id = get_connection_id()
logging.info(f"Using connection ID: {connection_id}")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register get_registered_services with the listener itself
    await register_service(
        RegisterRequest(service_name="get_registered_services", url="http://localhost:8001/get_registered_services"))

    # Setup code here
    proxy_url = f"ws://localhost:8080/ws/{connection_id}"  # Adjust this URL as needed
    logging.info(f"Listener: Starting to schedule subscribe_to_proxy task with URL {proxy_url} and connection ID {connection_id}")
    asyncio.create_task(subscribe_to_proxy(proxy_url, connection_id))
    yield
    # Cleanup code here
    logging.info("Listener: Shutting down and cleaning up")

app = FastAPI(lifespan=lifespan)

async def subscribe_to_proxy(proxy_url, connection_id):
    logging.info(f"listener: subscribe_to_proxy: Attempting to connect to proxy at {proxy_url} with connection ID {connection_id}")

    try:
        async with websockets.connect(proxy_url) as websocket:
            logging.info(f"Listener: Connected to proxy, sending registration with connection ID {connection_id}")
            await websocket.send(json.dumps({"action": "register", "connection_id": connection_id}))
            logging.info(f"Listener: Registered with proxy {proxy_url} using connection ID {connection_id}")

            try:
                while True:
                    envelope_str = await websocket.recv()
                    logging.info(f"Listener: Received envelope from proxy: {envelope_str}")
                    envelope = Envelope.parse_raw(envelope_str)
                    try:
                        response = await forward_request(envelope)
                        logging.info(f"Listener: Received response from forward_request: {response}")
                        await websocket.send(json.dumps(response))
                    except HTTPException as e:
                        logging.error(f"Listener: subscribe_to_proxy: Service Not Registered: {envelope.endpoint_service_name}: {str(e)}")
                        await websocket.send(json.dumps(f"Listener: subscribe_to_proxy: Service Not Registered: {envelope.endpoint_service_name}: {str(e)}"))
                    except requests.RequestException as e:
                        logging.error(f"Listener: Error forwarding request to {envelope_str}: {str(e)}")
                        await websocket.send(json.dumps({"error": str(e)}))
            except WebSocketDisconnect:
                logging.info("Listener: WebSocket disconnected")
    except Exception as e:
        logging.error(f"Listener: Failed to connect to proxy: {str(e)}")

@app.websocket("/ws")
async def websocket_forwarder(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            envelope_str = await websocket.receive_text()
            envelope = Envelope.parse_raw(envelope_str)
            try:
                response = requests.request(
                    method=envelope.endpoint_request_type,
                    url=envelope.endpoint_url,
                    headers=envelope.endpoint_headers,
                    params=envelope.endpoint_params,
                    json=envelope.endpoint_body
                )
                await websocket.send(response.text)
            except requests.RequestException as e:
                await websocket.send(json.dumps({"error": str(e)}))
    except WebSocketDisconnect:
        pass

@app.post("/forward")
async def forward_request(envelope: Envelope):
    logging.debug(f"forward_request: Received envelope : {envelope}")
    service_name = envelope.endpoint_service_name
    logging.debug(f"forward_request: service_name : {service_name}")
    if service_name in service_registry:
        # Forward to the registered endpoint
        url = service_registry[service_name]
        try:
            logging.info(f"Attempting to call : {service_name}: {envelope}")

            response = requests.request(
                method=envelope.endpoint_request_type,
                url=f"{url}/{service_name}",  # Append the endpoint to the base URL
                headers=envelope.endpoint_headers,
                params=envelope.endpoint_params,
                json=envelope.endpoint_body
            )
            logging.info(f"forward_request: response : {response}")

            return response.json()
        except requests.RequestException as e:
            raise HTTPException(status_code=500, detail=str(e))
    else:
        logging.error(f"forward_request: service_name : {service_name} not in {service_registry}")
        raise HTTPException(status_code=400, detail="Service not registered")

@app.post("/register")
async def register_service(request: RegisterRequest):
    service_registry[request.service_name] = request.url
    # Cascade registration to the proxy
    proxy_registration = {
        "service_name": request.service_name,
        "url": request.url,
        "connection_id": connection_id
    }
    try:
        response = requests.post(PROXY_URL, json=proxy_registration)
        response.raise_for_status()
    except requests.RequestException as e:
        logging.error(f"Failed to register service with proxy: {e}")
        raise HTTPException(status_code=500, detail="Failed to register service with proxy")
    return {"message": "Service registered successfully"}

@app.post("/deregister")
async def deregister_service(request: DeregisterRequest):
    if request.service_name in service_registry:
        del service_registry[request.service_name]
        # Cascade deregistration to the proxy
        proxy_deregistration = {
            "service_name": request.service_name,
            "connection_id": connection_id
        }
        try:
            response = requests.post(DEREGISTER_PROXY_URL, json=proxy_deregistration)
            response.raise_for_status()
        except requests.RequestException as e:
            logging.error(f"Failed to deregister service with proxy: {e}")
            raise HTTPException(status_code=500, detail="Failed to deregister service with proxy")
        return {"message": "Service deregistered successfully"}
    else:
        raise HTTPException(status_code=400, detail="Service not found")


@app.get("/get_registered_services")
async def get_registered_services():
    logging.info(f"Listener:  get_service_registry: {service_registry}")
    return service_registry

@app.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    openapi_json = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    return yaml.dump(openapi_json, default_flow_style=False)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
