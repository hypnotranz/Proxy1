import logging
import httpx
from fastapi import APIRouter, HTTPException, Depends, Request
from models.envelope import Envelope
from models.register_request import RegisterRequest
from models.deregister_request import DeregisterRequest
from services.forward_service import ForwardService
from services.registry_service import RegistryService
from config.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

def get_services(request: Request):
    logger.info("Retrieving services from app state")
    service_registry = request.app.state.service_registry
    connection_id = request.app.state.connection_id

    forward_service = ForwardService(settings.forward_service_url)
    registry_service = RegistryService(service_registry, connection_id)
    logger.info("Services retrieved successfully")
    return forward_service, registry_service

@router.post("/forward")
async def forward_request(envelope: Envelope, services=Depends(get_services)):
    forward_service, _ = services
    logger.info(f"Received forward request: {envelope}")
    response = await forward_service.forward_request(envelope)
    logger.info(f"Forward request response: {response}")
    return response

@router.post("/register")
async def register_service(request: RegisterRequest, services=Depends(get_services)):
    _, registry_service = services
    logger.info(f"Received register service request: {request}")
    response = await registry_service.register_service(request)
    logger.info(f"Register service response: {response}")
    return response

@router.post("/deregister")
async def deregister_service(request: DeregisterRequest, services=Depends(get_services)):
    _, registry_service = services
    logger.info(f"Received deregister service request: {request}")
    response = await registry_service.deregister_service(request)
    logger.info(f"Deregister service response: {response}")
    return response

@router.get("/get_registered_services")
async def get_registered_services(services=Depends(get_services)):
    _, registry_service = services
    logger.info("Received get registered services request")
    response = await registry_service.get_registered_services()
    logger.info(f"Get registered services response: {response}")
    return response

@router.get("/get_service_url/{service_name}")
async def get_service_url(service_name: str, services=Depends(get_services)):
    _, registry_service = services
    logger.info(f"Received get service URL request for: {service_name}")
    response = await registry_service.get_service_base_url(service_name)
    if response:
        logger.info(f"Get service URL response: {response}")
        return {"service_name": service_name, "url": response}
    else:
        logger.warning(f"Service not found: {service_name}")
        raise HTTPException(status_code=404, detail="Service not found")


@router.get("/openapi.yaml", include_in_schema=False)
async def get_openapi_yaml():
    logger.info("Received request for openapi.yaml")
    openapi_json = {
        "title": "WebSocket Listener Service",
        "version": "1.0.0",
        "openapi_version": "3.0.0",
        "description": "API for the WebSocket Listener Service",
        "routes": [route.path for route in router.routes]
    }
    logger.info("Returning openapi.yaml")
    return openapi_json
