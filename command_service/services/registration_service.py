import httpx
from fastapi import HTTPException
from services.logger import CustomLogger, log_decorator
from config.config import Settings
import logging
from models.register_request import RegisterRequest
import os

class RegistrationService:
    def __init__(self, settings: Settings, logger: CustomLogger):
        self.settings = settings
        self.logger = logger

    @log_decorator()
    async def register_service(self):
        command_service_ip = self.settings.command_service_ip

        registration_data = RegisterRequest(
            service_name=self.settings.service_name,
            openapi_url=f'http://{command_service_ip}:{self.settings.port}/openapi.json'
        )
        self.logger.error(f'http://{command_service_ip}:{self.settings.port}/openapi.json')
        timeout = httpx.Timeout(10.0, connect=10.0)  # Define timeout

        try:
            self.logger.log(logging.ERROR, f'Registering service with the proxy...{registration_data.dict()}')
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(self.settings.proxy_url, json=registration_data.dict())
                response.raise_for_status()
            self.logger.log(logging.ERROR, 'Service registered successfully with the proxy.')
        except httpx.RequestError as e:
            self.logger.log(logging.ERROR, f'Failed to register service with proxy: {e}')
            raise HTTPException(status_code=500, detail='Failed to register service with proxy')
