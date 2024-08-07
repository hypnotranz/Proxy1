import unittest
from unittest.mock import patch, AsyncMock
from services.command_service import run_command
from command_service import Settings
import logging
import asyncio

class TestCommandService(unittest.TestCase):
    def setUp(self):
        config_data = {
            "proxy_url": "http://localhost:8010/register",
            "host": "0.0.0.0",
            "port": 8003,
            "service_name": "execute-bash",
            "logging_level": "INFO",
            "logging_format": "{asctime} {correlation_id} {codefile} {methodname} {parameters} {message}",
            "logging_sinks": ["console"],
            "elastic_url": "http://localhost:9200/logs"
        }
        self.settings = Settings(**config_data)
        self.logger = logging.getLogger("custom_logger")

    @patch("asyncio.create_subprocess_shell")
    def test_run_command_success(self, mock_subprocess):
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"output", b"")
        mock_subprocess.return_value = mock_process

        command = "echo test"
        path = ""
        stdout, stderr = asyncio.run(run_command(command, path, self.settings, self.logger))

        self.assertEqual(stdout, "output")
        self.assertEqual(stderr, "")

    @patch("asyncio.create_subprocess_shell")
    def test_run_command_failure(self, mock_subprocess):
        mock_process = AsyncMock()
        mock_process.communicate.return_value = (b"", b"error")
        mock_subprocess.return_value = mock_process

        command = "wrongcommand"
        path = ""
        stdout, stderr = asyncio.run(run_command(command, path, self.settings, self.logger))

        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "error")

if __name__ == "__main__":
    unittest.main()
