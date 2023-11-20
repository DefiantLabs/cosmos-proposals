import argparse
from config import Config
from chain_registry import ChainRegistry

def get_app_args():
    parser = argparse.ArgumentParser(description="Cosmos proposal Slack monitor")
    parser.add_argument('--config', default='./config.json')
    return parser.parse_args()

def main():
    args = get_app_args()

    config = Config(args.config)

    chain_registry = ChainRegistry(zip_location=config.chain_registry_zip_location)

    for chain in config.chains["mainnet"]:
        chain = chain_registry.get_chain(chain)
        print(chain.get_healthy_rest_servers())


if __name__ == '__main__':
    main()