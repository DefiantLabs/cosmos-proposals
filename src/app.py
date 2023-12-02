import argparse
from config import Config
from chain_registry import ChainRegistry, Chain as ChainRegistryChain
from mongo import get_client as get_mongo_client, get_database as get_mongo_database, SlackChannel, Chain, Proposal
from datetime import datetime
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time
from concurrent.futures import ThreadPoolExecutor
from utils.lists import chunks
import os

from log import get_configured_logger

def get_app_base_env():
    # get config file path from ENV
    config_path = os.environ.get("CONFIG_PATH", None)
    return {
        "config": config_path
    }


def get_app_args():
    parser = argparse.ArgumentParser(description="Cosmos proposal Slack monitor")
    parser.add_argument('--config', default=None)
    return parser.parse_args()

def main():

    env_args = get_app_base_env()

    args = get_app_args()

    config_location = "./config.json"

    # prefer cli arg over env arg for config location
    if args.config is not None:
        config_location = args.config
    elif env_args["config"] is not None:
        config_location = env_args["config"]
        

    config = Config(config_location)

    logger = get_configured_logger(__name__, config.log_level, "")

    mongo_client = get_mongo_client(config.mongo_uri)

    mongo_db = get_mongo_database(mongo_client)

    chain_registry = ChainRegistry(zip_location=config.chain_registry_zip_location, log_level=config.log_level, rest_overides=config.chain_registry_rest_overides)

    if config.do_slack:
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
    for chain in config.chains:
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
        loop_start_time = time.time()
        notifications_needed = []

        # The active proposals data requests are done in chunks and threaded to speed up the process
        # The number of threads is set in the config
        # This is better optimized since the active proposal data requests are IO heavy and not CPU heavy
        for chunk in chunks(list(chains.items()), config.main_loop["proposal_workers"]):
            logger.info(f"Requesting active proposals for chain chunk {list(map(lambda chain: chain[0], chunk))}")
            with ThreadPoolExecutor(max_workers=config.main_loop["proposal_workers"]) as executor:
                executions = []
                for chain in chunk:
                    logger.debug(f"Submitting active proposals job for chain {chain[0]}")
                    executions.append(executor.submit(get_chain_active_proposals, chain[0], chain[1]["chain_registry_entry"], chain[1]["chain_object"]))
                responses = [execution.result() for execution in executions]

            for response in responses:
                if response["error"] is not None:
                    logger.error(f"Unable to get active proposals for chain {response['chain'][0]}")
                    logger.error(f"Error: {response['error']}")
                    continue

                active_proposals = response["active_proposals"]
                chain_name = response["chain_name"]

                chain_registry_entry = response["chain_registry_entry"]
                chain_object = response["chain_object"]

                for proposal in active_proposals["proposals"]:

                    logger.info(f"Found active proposal {proposal['proposal_id']} on chain {chain_name}")

                    proposal_object = Proposal(mongo_db).find_or_create_proposal_by_chain_and_id(chain_object._id, proposal["proposal_id"])
                    submit_time = proposal_object.get_or_set_proposal_submit_time(datetime.strptime(proposal["submit_time"].split(".")[0], "%Y-%m-%dT%H:%M:%S"))

                    logger.info(f"Proposal {proposal['proposal_id']} submit time is {submit_time}")
                    
                    if not channel.is_proposal_notified(proposal_object._id):
                        logger.info(f"Proposal {proposal['proposal_id']} is new, sending notification")
                        text, blocks = get_new_proposal_slack_notification(chain_registry_entry, proposal)
                        logger.debug(f"Text: {text}")
                        logger.debug(f"Blocks: {blocks}")
                        notifications_needed.append({
                            "proposal_id": proposal["proposal_id"],
                            "proposal_object": proposal_object,
                            "text": text,
                            "blocks": blocks,
                            "chain_registry_entry": chain_registry_entry,
                            "chain_object": chain_object,
                            "chain_name": chain_name
                        })
                        
                    else:
                        logger.info(f"Proposal {proposal['proposal_id']} has already been notified, skipping")

        if len(notifications_needed) == 0:
            logger.info("No new proposal notifications needed")
        else:
            for notification in notifications_needed:
                chain_name = notification["chain_registry_entry"].pretty_name
                chain_id = notification["chain_registry_entry"].chain_id
                logger.info(f"Sending notification for proposal {notification['proposal_id']} on chain {chain_name} ({chain_id})")
                try:
                    if config.do_slack:
                        slack_client.chat_postMessage(
                            channel=config.slack_channel_id,
                            text=notification["text"],
                            blocks=notification["blocks"],
                            unfurl_links=False,
                        )
                except SlackApiError as e:
                    logger.error(f"Error sending Slack notification: {e.response['error']}")
                else:
                    channel.set_proposal_notified(notification["proposal_object"]._id)
                    logger.info(f"Proposal {notification['proposal_id']} notified")
                    time.sleep(10)

        loop_end_time = time.time()
        loop_time = loop_end_time - loop_start_time

        logger.info(f"Main loop finished in {round(loop_time, 2)} seconds, sleeping for {config.main_loop['sleep_time']} seconds")

        time.sleep(config.main_loop["sleep_time"])

def get_chain_active_proposals(chain_name: str, chain_registry_entry: ChainRegistryChain, chain_object: Chain):
    try:
        return {"error": None, "active_proposals": chain_registry_entry.get_active_proposals(), "chain_name": chain_name, "chain_object": chain_object, "chain_registry_entry": chain_registry_entry}
    except Exception as e:
        return {"error": e, "active_proposals": None, "chain_name": chain_name, "chain_object": chain_object, "chain_registry_entry": chain_registry_entry}

def get_new_proposal_slack_notification(chain_registry_entry: ChainRegistryChain, proposal):

    mintscan_chain_explorer = chain_registry_entry.get_explorer(explorer_name="mintscan")

    explorer_link = None
    if mintscan_chain_explorer is not None:
        explorer_url = f"{mintscan_chain_explorer['url']}/proposals/{proposal['proposal_id']}"
        explorer_link = {
			"type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<{explorer_url}|View on Mintscan>"
            }
        }
    elif mintscan_chain_explorer is None and chain_registry_entry.chain_id == "pirin-1":
        ping_pub_chain_explorer = chain_registry_entry.get_explorer(explorer_name="ping.pub")
        explorer_url = f"{ping_pub_chain_explorer['url']}/gov/{proposal['proposal_id']}"
        explorer_link = {
			"type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"<{explorer_url}|View on Ping.pub>"
            }
        }

    chain_name = chain_registry_entry.pretty_name
    chain_id = chain_registry_entry.chain_id

    try:
        title = proposal['content']['title']
    except:
        title = f"No title (Type is {proposal['content']['@type']})"

    description = ""
    try:
        description = proposal['content']['description']

        if len(description) > 300:
            description = description[:300] + "..."
    except:
        pass

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f":mega: New proposal on {chain_name} ({chain_id})"
		    }
	    },
        {
			"type": "divider"
		},
        {
			"type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"#{proposal['proposal_id']}. {title}"
            }
        },
    ]

    if description != "":
        blocks.append({
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": description
            }
        })


    if explorer_link is not None:
        blocks.append(explorer_link)

    text = f"New proposal on {chain_name} ({chain_id}): #{proposal['proposal_id']}. {title}"

    return text, blocks


if __name__ == '__main__':
    main()