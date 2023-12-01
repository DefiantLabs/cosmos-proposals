import argparse
from config import Config
from chain_registry import ChainRegistry, Chain as ChainRegistryChain
from mongo import get_client as get_mongo_client, get_database as get_mongo_database, SlackChannel, Chain, Proposal
from datetime import datetime
import logging
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError
import time

from log import get_configured_logger

def get_app_args():
    parser = argparse.ArgumentParser(description="Cosmos proposal Slack monitor")
    parser.add_argument('--config', default='./config.json')
    return parser.parse_args()

def main():

    args = get_app_args()

    config = Config(args.config)

    logger = get_configured_logger(__name__, config.log_level, "")

    mongo_client = get_mongo_client(config.mongo_uri)

    mongo_db = get_mongo_database(mongo_client)

    chain_registry = ChainRegistry(zip_location=config.chain_registry_zip_location, log_level=config.log_level)

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
        for chain_name, chain in chains.items():
            logger.info(f"Requesting active proposals for chain {chain_name}")
            try:
                active_proposals = chain["chain_registry_entry"].get_active_proposals()
            except Exception as e:
                logger.error(f"Unable to get active proposals for chain {chain_name}")
                logger.error(f"Error: {e}")
                continue

            for proposal in active_proposals["proposals"]:

                logger.info(f"Found active proposal {proposal['proposal_id']} on chain {chain_name}")

                proposal_object = Proposal(mongo_db).find_or_create_proposal_by_chain_and_id(chain["chain_object"]._id, proposal["proposal_id"])
                submit_time = proposal_object.get_or_set_proposal_submit_time(datetime.strptime(proposal["submit_time"].split(".")[0], "%Y-%m-%dT%H:%M:%S"))

                logger.info(f"Proposal {proposal['proposal_id']} submit time is {submit_time}")
                
                if not channel.is_proposal_notified(proposal_object._id):
                    logger.info(f"Proposal {proposal['proposal_id']} is new, sending notification")
                    text, blocks = get_new_proposal_slack_notification(chain["chain_registry_entry"], proposal)
                    logger.debug(f"Text: {text}")
                    logger.debug(f"Blocks: {blocks}")
                    try:
                        slack_client.chat_postMessage(
                            channel=config.slack_channel_id,
                            text=text,
                            blocks=blocks,
                            unfurl_links=False,
                        )
                    except SlackApiError as e:
                        logger.error(f"Error sending Slack notification: {e.response['error']}")
                    else:
                        channel.set_proposal_notified(proposal_object._id)
                        logger.info(f"Proposal {proposal['proposal_id']} notified")
                        time.sleep(10)
                else:
                    logger.info(f"Proposal {proposal['proposal_id']} has already been notified, skipping")

                    

        logger.info("Main loop finished, sleeping")
        time.sleep(60)

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