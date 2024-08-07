import logging
from elasticsearch import Elasticsearch
from datetime import datetime

class ElasticsearchHandler(logging.Handler):
    def __init__(self, hosts, index):
        super().__init__()
        self.es = Elasticsearch(hosts)
        self.index = index

    def emit(self, record):
        log_entry = self.format(record)
        self.es.index(index=self.index, body={
            '@timestamp': datetime.utcnow().isoformat(),
            'message': log_entry,
            'level': record.levelname,
            'logger': record.name,
        })

def configure_logging(logger_name, es_hosts, es_index):
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.INFO)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    # Elasticsearch handler
    es_handler = ElasticsearchHandler(es_hosts, es_index)
    es_handler.setLevel(logging.INFO)
    es_handler.setFormatter(console_formatter)
    logger.addHandler(es_handler)

    return logger
