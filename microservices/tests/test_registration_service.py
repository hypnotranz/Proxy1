import unittest
from unittest.mock import patch, AsyncMock
from command_service import RegistrationService
from command_service import Settings
from services.logger import CustomLogger
import asyncio
import httpx
from fastapi import HTTPException

class TestRegistrationService(unittest.TestCase):
    def setUp(self):
        config_data = {
            "proxy_url": "http://localhost:8010/register",
            "host": "0.0.0.0",
            "port": 8003,
            "service_name": "execute-bash",
            "logging_level": "INFO",
            "logging_format": "{asctime} {message}",
            "logging_sinks": ["console"],
            "elastic_url": "http://localhost:9200/logs"
        }
        self.settings = Settings(**config_data)
        self.logger = CustomLogger(self.settings)

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    @patch.object(CustomLogger, "log")
    def test_register_service_success(self, mock_log, mock_post):
        mock_post.return_value.status_code = 200

        registration_service = RegistrationService(self.settings, self.logger)
        result = asyncio.run(registration_service.register_service())

        self.assertIsNone(result)
        mock_post.assert_called_once_with(self.settings.proxy_url, json={
            "service_name": self.settings.service_name,
            "url": f"http://{self.settings.host}:{self.settings.port}"
        })

    @patch("httpx.AsyncClient.post", new_callable=AsyncMock)
    @patch.object(CustomLogger, "log")
    def test_register_service_failure(self, mock_log, mock_post):
        mock_post.side_effect = httpx.RequestError("Failed to register service with proxy", request=object())

        registration_service = RegistrationService(self.settings, self.logger)

        with self.assertRaises(HTTPException):
            asyncio.run(registration_service.register_service())

        mock_post.assert_called_once_with(self.settings.proxy_url, json={
            "service_name": self.settings.service_name,
            "url": f"http://{self.settings.host}:{self.settings.port}"
        })

if __name__ == "__main__":
    unittest.main()

