import argparse
from config import Config
from chain_registry import ChainRegistry
from mongo import get_client as get_mongo_client, get_database as get_mongo_database, SlackChannel, Chain, Proposal
from datetime import datetime
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
from pprint import pprint
import time


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

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

    channel = SlackChannel(mongo_db).find_or_create_channel_by_id(config.slack_channel_id)

    chains = {}
    for chain in config.chains["mainnet"]:
        chain_registry_entry = chain_registry.get_chain(chain)
        chain_object = Chain(mongo_db).find_or_create_chain_by_name(chain)
        chains[chain] = {
            "chain_registry_entry": chain_registry_entry,
            "chain_object": chain_object
        }

    # main loop, does the following:
    # - check for new proposals
    # - checks if those proposals have already had notifications sent for them
    # - sends notifications for proposals that have not had notifications sent for them
    logger.info("Starting main loop")
    while True:
        for chain_name, chain in chains.items():
            logger.info(f"Requesting active proposals for chain {chain_name}")
            active_proposals = chain["chain_registry_entry"].get_active_proposals()

            for proposal in active_proposals["proposals"]:
                proposal_object = Proposal(mongo_db).find_or_create_proposal_by_chain_and_id(chain["chain_object"]._id, proposal["proposal_id"])
                submit_time = datetime.strptime(proposal["submit_time"].split(".")[0], "%Y-%m-%dT%H:%M:%S")
                proposal_object.get_or_set_proposal_submit_time(submit_time)

        logger.info("Main loop finished, sleeping")
        time.sleep(30)

if __name__ == '__main__':
    main()