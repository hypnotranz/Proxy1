import logging
import json
import os
from pydantic import BaseSettings, Field
from typing import List
import socket

def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Use Google's public DNS server to find the local IP address
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except Exception as e:
        print(f"Error getting host IP: {e}")
        ip = '127.0.0.1'
    finally:
        s.close()
    return ip

class Settings(BaseSettings):
    proxy_url: str
    host: str
    port: int
    service_name: str
    forward_service_url: str
    logging_level: str
    logging_format: str
    logging_sinks: List[str] = Field(default_factory=list)
    elastic_url: str
    command_service_ip: str
    bash_working_directory: str



def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    logging.info(f"Loading configuration from {config_path}")

    with open(config_path) as config_file:
        config_data = json.load(config_file)
        logging.info(f"Config Data Loaded: {config_data}")

        forward_service_url = os.getenv('FORWARD_SERVICE_URL', config_data.get('forward_service_url'))
        logging.info(f"FORWARD_SERVICE_URL: {forward_service_url}")

        # Handle LOGGING_SINKS environment variable
        logging_sinks_env = os.getenv('LOGGING_SINKS')
        if logging_sinks_env:
            logging.info(f"Parsing LOGGING_SINKS from environment variable: {logging_sinks_env}")
            try:
                logging_sinks = json.loads(logging_sinks_env)
            except json.JSONDecodeError as e:
                logging.error(f"Error parsing LOGGING_SINKS environment variable: {e}")
                logging_sinks = config_data['logging']['sinks']
        else:
            logging_sinks = config_data['logging']['sinks']

        return Settings(
            proxy_url=os.getenv('PROXY_URL', config_data['proxy_url']),
            host=os.getenv('HOST', config_data['host']),
            port=int(os.getenv('PORT', config_data['port'])),
            service_name=os.getenv('SERVICE_NAME', config_data['service_name']),
            forward_service_url=forward_service_url,
            logging_level=os.getenv('LOGGING_LEVEL', config_data['logging']['level']),
            logging_format=os.getenv('LOGGING_FORMAT', config_data['logging']['format']),
            logging_sinks=logging_sinks,
            elastic_url=os.getenv('ELASTIC_URL', config_data['logging']['elastic_url']),
            command_service_ip=os.getenv('COMMAND_SERVICE_IP', get_host_ip()),
            bash_working_directory=config_data['bash_working_directory']

        )


settings = load_config()

# Configure logging
logging.basicConfig(level=settings.logging_level, format=settings.logging_format)
logger = logging.getLogger(settings.service_name)
logger.info(f"Configuration Loaded: {settings.dict()}")
