import json, os

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

        if "slack_channel_id" in self.config:
            self.slack_channel_id = self.config["slack_channel_id"]
        else:
            raise Exception("slack_channel_id not set in config")

        self.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN", None)

        if self.slack_bot_token is None:
            raise Exception("SLACK_BOT_TOKEN environment variable not set")

    def load_config(self):
        with open(self.config_file) as f:
            return json.load(f)