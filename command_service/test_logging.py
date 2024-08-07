import logging

logging.basicConfig(level=logging.DEBUG, format='{asctime} {name} {levelname} {message}', style='{')
logger = logging.getLogger('test_logger')

logger.debug('This is a DEBUG message')
logger.info('This is an INFO message')
logger.warning('This is a WARNING message')
logger.error('This is an ERROR message')
logger.critical('This is a CRITICAL message')
