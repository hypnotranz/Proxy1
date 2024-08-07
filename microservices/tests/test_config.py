import unittest
import command_service
from unittest.mock import patch, mock_open

class TestConfig(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data="{\"proxy_url\": \"http://localhost:8010/register\", \"host\": \"0.0.0.0\", \"port\": 8003, \"service_name\": \"execute-bash\", \"logging\": {\"level\": \"INFO\", \"format\": \"{asctime} {correlation_id} {codefile} {methodname} {parameters} {message}\", \"sinks\": [\"console\"], \"elastic_url\": \"http://localhost:9200/logs\"}}")
    def test_load_config(self, mock_file):
        settings = load_config()
        self.assertEqual(settings.proxy_url, "http://localhost:8010/register")
        self.assertEqual(settings.host, "0.0.0.0")
        self.assertEqual(settings.port, 8003)
        self.assertEqual(settings.service_name, "execute-bash")
        self.assertEqual(settings.logging_level, "INFO")
        self.assertEqual(settings.logging_format, "{asctime} {correlation_id} {codefile} {methodname} {parameters} {message}")
        self.assertEqual(settings.logging_sinks, ["console"])
        self.assertEqual(settings.elastic_url, "http://localhost:9200/logs")

if __name__ == "__main__":
    unittest.main()
