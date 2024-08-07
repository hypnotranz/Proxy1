import logging
from datetime import datetime
import json
from concurrent.futures import ThreadPoolExecutor
import requests

class ElasticsearchHandler(logging.Handler):
    def __init__(self, elastic_url):
        super().__init__()
        self.elastic_url = elastic_url
        self.executor = ThreadPoolExecutor(max_workers=1)

    def emit(self, record):
        log_entry = self.format(record)
        self.executor.submit(self.send_to_elasticsearch, log_entry, record)

    def send_to_elasticsearch(self, log_entry, record):
        try:
            log_message = {
                "@timestamp": datetime.utcnow().isoformat(),
                "message": log_entry,
                "level": record.levelname,
                "logger_name": record.name
            }
            print(f"Sending log to Elasticsearch: {json.dumps(log_message, indent=2)}")  # Debug print
            response = requests.post(
                f"{self.elastic_url}/logs/_doc",
                headers={"Content-Type": "application/json"},
                json=log_message
            )
            response.raise_for_status()
        except requests.HTTPError as e:
            print(f"Failed to send log to Elasticsearch: {e.response.status_code} {e.response.reason}")
            print(f"Response content: {e.response.content}")
        except json.JSONDecodeError as e:
            print(f"JSON decoding error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

class CustomLogger:
    def __init__(self, settings):
        self.logger = logging.getLogger('custom_logger')
        if not self.logger.hasHandlers():
            self.logger.setLevel(logging.DEBUG)  # Ensure logger level is set to DEBUG
            formatter = logging.Formatter(settings.logging_format, style='{')

            if 'console' in settings.logging_sinks:
                console_handler = logging.StreamHandler()
                console_handler.setLevel(logging.DEBUG)  # Ensure handler level is set to DEBUG
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)

            if 'file' in settings.logging_sinks:
                file_handler = logging.FileHandler('app.log')
                file_handler.setLevel(logging.DEBUG)  # Ensure handler level is set to DEBUG
                file_handler.setFormatter(formatter)
                self.logger.addHandler(file_handler)

            if 'elastic' in settings.logging_sinks:
                elastic_handler = ElasticsearchHandler(settings.elastic_url)
                elastic_handler.setLevel(logging.DEBUG)  # Ensure handler level is set to DEBUG
                elastic_handler.setFormatter(formatter)
                self.logger.addHandler(elastic_handler)

    def log(self, level, msg, *args, **kwargs):
        self.logger.log(level, msg, *args, **kwargs)

    def debug(self, msg, *args, **kwargs):
        self.logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self.logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self.logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self.logger.error(msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        self.logger.critical(msg, *args, **kwargs)

def get_logger(settings):
    return CustomLogger(settings)

def log_decorator(log_parameters=True):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            logger = kwargs.get('logger', None)
            if not logger:
                logger = logging.getLogger('custom_logger')
                if not logger.hasHandlers():
                    logger.setLevel(logging.INFO)
                    console_handler = logging.StreamHandler()
                    formatter = logging.Formatter('{asctime} {message}', style='{')
                    console_handler.setFormatter(formatter)
                    logger.addHandler(console_handler)
            if log_parameters:
                params = {**kwargs}
            else:
                params = {}
            logger.info(f'Entering {func.__name__}')
            result = await func(*args, **kwargs)
            logger.info(f'Exiting {func.__name__}')
            return result
        return wrapper
    return decorator
