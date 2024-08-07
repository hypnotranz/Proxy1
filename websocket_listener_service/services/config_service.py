import json
import logging
import os
import uuid

class ConfigService:
    CONFIG_FILE = "config.json"

    def load_config(self):
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as file:
                logging.info("Loading configuration from file")
                return json.load(file)
        return {}

    def save_config(self, config):
        with open(self.CONFIG_FILE, "w") as file:
            json.dump(config, file)

    def get_connection_id(self):
        config = self.load_config()
        if "connection_id" not in config:
            config["connection_id"] = str(uuid.uuid4())
            self.save_config(config)
        return config["connection_id"]
