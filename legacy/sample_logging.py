import logging
import time
from logging_config import configure_logging

# Configure logging
logger = configure_logging('sample_logger', ['http://localhost:9200'], 'sample-logs')

# Sample logging
for i in range(10):
    logger.info(f'Logging info message {i}')
    logger.warning(f'Logging warning message {i}')
    logger.error(f'Logging error message {i}')
    time.sleep(1)
