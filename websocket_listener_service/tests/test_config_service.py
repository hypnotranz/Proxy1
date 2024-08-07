import os
import json
import pytest
from unittest.mock import patch, mock_open
from websocket_listener_service.services.config_service import ConfigService

@pytest.fixture
def config_service():
    return ConfigService()

def test_load_config(config_service):
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="{\"connection_id\": \"12345\"}")):
            config = config_service.load_config()
            assert config["connection_id"] == "12345"

def test_save_config(config_service):
    with patch("builtins.open", mock_open()) as mocked_file:
        config = {"connection_id": "12345"}
        config_service.save_config(config)
        mocked_file().write.assert_called_once_with(json.dumps(config))

def test_get_connection_id_existing(config_service):
    with patch("os.path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="{\"connection_id\": \"12345\"}")):
            connection_id = config_service.get_connection_id()
            assert connection_id == "12345"

def test_get_connection_id_new(config_service):
    with patch("os.path.exists", return_value=False):
        with patch("builtins.open", mock_open()):
            with patch("uuid.uuid4", return_value="12345"):
                connection_id = config_service.get_connection_id()
                assert connection_id == "12345"

