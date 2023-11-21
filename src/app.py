import argparse
from config import Config
from chain_registry import ChainRegistry
from mongo import get_client as get_mongo_client, get_database as get_mongo_database, Channel

import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pprint import pprint

logger = logging.getLogger(__name__)


def get_app_args():
    parser = argparse.ArgumentParser(description="Cosmos proposal Slack monitor")
    parser.add_argument('--config', default='./config.json')
    return parser.parse_args()

def main():
    args = get_app_args()

    config = Config(args.config)

    chain_registry = ChainRegistry(zip_location=config.chain_registry_zip_location)

    mongo_client = get_mongo_client(config.mongo_uri)

    mongo_db = get_mongo_database(mongo_client)


    slack_client = WebClient(token=config.slack_bot_token, logger=logger)
    
    configured_channel = None

    for result in slack_client.conversations_list(types="public_channel, private_channel"):
        for channel in result["channels"]:
            if channel["id"] == config.slack_channel_id:
                configured_channel = channel
                break

    if configured_channel is None:
        raise Exception(f"Unable to find configured slack channel {config.slack_channel_id}")
    
    if not configured_channel["is_member"]:
        raise Exception(f"Slack bot is not a member of configured slack channel {config.slack_channel_id}")
    
    if configured_channel["is_archived"]:
        raise Exception(f"Configured slack channel {config.slack_channel_id} is archived")

    channel = Channel(mongo_db).find_or_create_channel_by_id(config.slack_channel_id)
    
if __name__ == '__main__':
    main()