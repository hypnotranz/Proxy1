import unittest
from unittest.mock import patch
from command_service import Settings
from services.logger import CustomLogger
import logging

class TestCustomLogger(unittest.TestCase):
    def setUp(self):
        self.config_data = {
            "proxy_url": "http://localhost:8010/register",
            "host": "0.0.0.0",
            "port": 8003,
            "service_name": "execute-bash",
            "logging_level": "INFO",
            "logging_format": "{asctime} {message}",
            "logging_sinks": ["console"],
            "elastic_url": "http://localhost:9200/logs"
        }
        self.settings = Settings(**self.config_data)

    @patch("logging.Logger.log")
    def test_logger_initialization(self, mock_log):
        custom_logger = CustomLogger(self.settings)
        self.assertIsInstance(custom_logger.logger, logging.Logger)
        self.assertEqual(custom_logger.logger.level, logging.INFO)

    @patch("logging.Logger.log")
    def test_log_method(self, mock_log):
        custom_logger = CustomLogger(self.settings)
        custom_logger.log(logging.INFO, "Test message", correlation_id="123")

        mock_log.assert_called_once()
        call_args = mock_log.call_args[0]
        self.assertEqual(call_args[0], logging.INFO)
        self.assertIn("Test message", call_args[1]["message"])

if __name__ == "__main__":
    unittest.main()

