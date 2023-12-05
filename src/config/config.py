import json, os
import logging

LOG_LEVEL = {
    "CRITICAL": logging.CRITICAL,
    "ERROR": logging.ERROR,
    "WARNING": logging.WARNING,
    "INFO": logging.INFO,
    "DEBUG": logging.DEBUG,
    "NOTSET": logging.NOTSET
}

class Config:
    def __init__(self, config_file):
        self.config_file = config_file
        self.config = self.load_config()

        self.chains = []

        if "logging" in self.config and "level" in self.config["logging"]:
            try:
                self.log_level = LOG_LEVEL[self.config["logging"]["level"]]
            except KeyError:
                raise Exception(f"Invalid log level in config, valid levels are {LOG_LEVEL.keys()}")
        else:
            self.log_level = logging.INFO

        if "chains" in self.config:
            self.chains = self.config["chains"]

        self.chain_registry_zip_location = None
        if "chain_registry_zip_location" in self.config:
            self.chain_registry_zip_location = self.config["chain_registry_zip_location"]

        self.chain_registry_rest_overides = {}
        
        if "chain_registry_rest_overides" in self.config:
            self.chain_registry_rest_overides = self.config["chain_registry_rest_overides"]


        self.slack_channel_id = os.environ.get("SLACK_CHANNEL_ID", None)
        if self.slack_channel_id is None:
            raise Exception("SLACK_CHANNEL_ID environment variable not set")
        
        self.slack_bot_token = os.environ.get("SLACK_BOT_TOKEN", None)

        if self.slack_bot_token is None:
            raise Exception("SLACK_BOT_TOKEN environment variable not set")
        
        self.mongo_user = os.environ.get("MONGO_USERNAME", None)
        self.mongo_password = os.environ.get("MONGO_PASSWORD", None)
        self.mongo_host = os.environ.get("MONGO_HOST", "localhost")
        self.mongo_port = os.environ.get("MONGO_PORT", "27017")

        if self.mongo_user is None:
            raise Exception("MONGO_USERNAME environment variable not set")
        
        if self.mongo_password is None:
            raise Exception("MONGO_PASSWORD environment variable not set")

        self.mongo_uri = f"mongodb://{self.mongo_user}:{self.mongo_password}@{self.mongo_host}:{self.mongo_port}"

        self.do_slack = True
        if "debugging" in self.config and "do_slack" in self.config["debugging"]:
            self.do_slack = self.config["debugging"]["do_slack"]

        self.main_loop = {
            "sleep_time": 60.0,
            "proposal_workers": 10
        }

        if "main_loop" in self.config:
            if "sleep_time" in self.config["main_loop"]:
                self.main_loop["sleep_time"] = float(self.config["main_loop"]["sleep_time"])
            if "proposal_workers" in self.config["main_loop"]:
                self.main_loop["proposal_workers"] = int(self.config["main_loop"]["proposal_workers"])

    def load_config(self):
        with open(self.config_file) as f:
            return json.load(f)