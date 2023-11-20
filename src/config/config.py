import json

class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()

        self.chains = {}
        if "chains" in self.config:
            self.chains = self.config["chains"]

        self.chain_registry_zip_location = None
        if "chain_registry_zip_location" in self.config:
            self.chain_registry_zip_location = self.config["chain_registry_zip_location"]

    def load_config(self):
        with open(self.config_file) as f:
            return json.load(f)