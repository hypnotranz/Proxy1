import logging
import asyncio
from fastapi import FastAPI, WebSocket
from controllers import listener_controller
from websocket.websocket_handler import WebSocketHandler
from models.register_request import RegisterRequest
from services.config_service import ConfigService
from services.registry_service import RegistryService
from config.config import settings, logger

app = FastAPI()

async def register_service():
    openapi_schema = app.openapi()

    # Hardcoding the servers field
    openapi_schema['servers'] = [{"url": f"http://{settings.host}:{settings.port}"}]
    app.openapi_schema = openapi_schema

    await asyncio.sleep(10)  # Wait for the server to be fully up and running

    registry_service = app.state.registry_service
    openapi_url = f"http://{settings.host}:{settings.port}/openapi.json"

    register_request = RegisterRequest(
        service_name=settings.service_name,
        openapi_url=openapi_url
    )
    await registry_service.register_service(register_request)
    logger.info(f"Service '{settings.service_name}' registered successfully.")

@app.on_event("startup")
async def startup_event():
    # Setup initial services and state
    service_registry = {}
    config_service = ConfigService()
    connection_id = config_service.get_connection_id()
    host = settings.host
    port = settings.port
    path = ""

    registry_service = RegistryService(service_registry, connection_id)
    app.state.service_registry = service_registry
    app.state.connection_id = connection_id
    app.state.registry_service = registry_service
    app.state.host = host
    app.state.port = port
    app.state.path = path

    # Setup WebSocketHandler
    websocket_handler = WebSocketHandler()
    app.state.websocket_handler = websocket_handler
    proxy_url = f"{settings.proxy_url}{connection_id}"
    logger.info(f"Listener: Starting to schedule subscribe_to_proxy task with URL {proxy_url} and connection ID {connection_id}")
    asyncio.create_task(websocket_handler.subscribe_to_proxy(proxy_url, connection_id))

    # Start the background task for service registration
    asyncio.create_task(register_service())

app.include_router(listener_controller.router)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await app.state.websocket_handler.websocket_endpoint(websocket, app.state.connection_id)

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting uvicorn server...")
    uvicorn.run(app, host=settings.host, port=settings.port)
