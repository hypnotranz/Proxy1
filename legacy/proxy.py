from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Any, Optional
import requests
import asyncio
import yaml
from fastapi.openapi.utils import get_openapi
import logging
from contextlib import asynccontextmanager

logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="Proxy Service API",
    description="API for the Proxy Service to forward requests to registered services",
    version="1.0.0",
)

class Envelope(BaseModel):
    endpoint_service_name: str = Field(..., description="Name of the service to forward the request to")
    endpoint_path: str = Field(..., description="Path of the service endpoint")
    endpoint_request_type: str = Field(..., description="HTTP method of the request (GET, POST, etc.)")
    endpoint_headers: Any = Field(default={}, description="Headers to include in the forwarded request")
    endpoint_params: Any = Field(default={}, description="Query parameters to include in the forwarded request")
    endpoint_body: Any = Field(default={}, description="Body of the forwarded request")
    connection_id: Optional[str] = Field(None, description="Connection ID for WebSocket listener")
    endpoint_url: str = Field(..., description="URL of the service to register")

class RegisterRequest(BaseModel):
    service_name: str = Field(..., description="Name of the service to register")
    url: str = Field(..., description="URL of the service to register")

websocket_clients = {}
service_registry = {}

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    openapi_schema["servers"] = [
        {"url": "https://katydid-glorious-slightly.ngrok-free.app"}
    ]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.openapi = custom_openapi
    yield
    # Cleanup code here if needed

app = FastAPI(lifespan=lifespan)

@app.post("/proxy", summary="Forward Request to Registered Service", description="Forward the request to the registered service.", operation_id="forward_request")
async def handle_proxy(envelope: Envelope):
    logging.info(f"Proxy: Incoming Message: {envelope}")

    service_name = envelope.endpoint_service_name
    if envelope.connection_id:
        # Handle forwarding via WebSocket listener

        if envelope.connection_id in websocket_clients:
            logging.info(f"Proxy: Destination Matches: {envelope}")

            ws = websocket_clients[envelope.connection_id]["websocket"]
            response_future = websocket_clients[envelope.connection_id]["response_future"]

            # Send the envelope to the WebSocket listener
            await ws.send_text(envelope.json())

            # Wait for the listener's response
            response = await response_future
            return response
        else:
            logging.error(f"WebSocket listener not found for {envelope.connection_id}")
            raise HTTPException(status_code=400, detail="WebSocket listener not found for connection_id.")
    elif service_name in service_registry:
        # Call the public REST endpoint
        try:
            base_url = service_registry[service_name]
            url = f"{base_url}/{envelope.endpoint_path.lstrip('/')}"  # Combine base URL with endpoint path
            response = requests.request(
                method=envelope.endpoint_request_type,
                url=url,
                headers=envelope.endpoint_headers,
                params=envelope.endpoint_params,
                json=envelope.endpoint_body
            )
            return response.json()
        except requests.RequestException as e:
            logging.info(f"Proxy: handle_proxy: Service {service_name} not registered in Proxy")
            raise HTTPException(status_code=500, detail=str(e))
    else:
        logging.info(f"Proxy: Missing connection_id or service_name.")
        raise HTTPException(status_code=400, detail="Proxy: Missing connection_id or service_name.")

@app.websocket("/ws/{connection_id}")
async def websocket_endpoint(websocket: WebSocket, connection_id: str):
    logging.info(f"Proxy: WebSocket connection established for {connection_id}")
    await websocket.accept()
    websocket_clients[connection_id] = {
        "websocket": websocket,
        "response_future": asyncio.Future()
    }
    try:
        while True:
            data = await websocket.receive_text()
            logging.info(f"Proxy: Received data from WebSocket client {connection_id}: {data}")
            if connection_id in websocket_clients:
                websocket_clients[connection_id]["response_future"].set_result(data)
                websocket_clients[connection_id]["response_future"] = asyncio.Future()
    except WebSocketDisconnect as e:
        logging.info(f"Proxy: WebSocket connection closed for {connection_id}: {e}")
        if connection_id in websocket_clients:
            del websocket_clients[connection_id]


@app.get("/openapi.yaml", include_in_schema=False, operation_id="get_openapi_yaml")
async def get_openapi_yaml():
    openapi_json = app.openapi()
    return yaml.dump(openapi_json, default_flow_style=False)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
