from fastapi import FastAPI
from services.registration_service import RegistrationService
from config.config import settings
from controllers import command_controller
import logging
import asyncio
import os
import uvicorn



logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.error("Logging started ...")

app = FastAPI()

@app.on_event("startup")
async def startup_event():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.error("Logging started ...")

    logger.error(f"Settings ... {settings}")

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.error("Logging started ...")

    logger.error("Application startup initiated")

    openapi_schema = app.openapi()
    command_service_ip = os.getenv('COMMAND_SERVICE_IP', 'localhost')
    openapi_schema['servers'] = [{"url": f"http://{command_service_ip}:{settings.port}"}]
    app.openapi_schema = openapi_schema
    logger.error("OpenAPI schema set")

    registration_service = RegistrationService(settings, logger)
    asyncio.create_task(registration_service.register_service())
    logger.info("Registration service started")

app.include_router(command_controller.router)

if __name__ == "__main__":
    logger.info("Starting the application")
    uvicorn.run(app, host=settings.host, port=settings.port)
