from rpc.requests import request_active_proposals
from chain_registry.chain_registry import ChainRegistry
import time

chain_registry = ChainRegistry(zip_location="./.venv/chain-registry-master.zip")

chains =  [
    #   "agoric",
    #   "akash",
    #   "celestia",
    #   "cosmoshub",
    #   "crescent",
    #   "dydx",
    #   "evmos",
    #   "injective",
      "juno",
    #   "nolus",
    #   "omniflixhub",
    #   "osmosis",
    #   "quasar",
    #   "sentinel",
    #   "stargaze"
]

for chain in chains:
    rpc_servers = chain_registry.get_chain(chain).get_rpc_servers()

    if len(rpc_servers) != 0:
        print(chain)
        print(rpc_servers)
        print(request_active_proposals(rpc_servers[0]))
        print()
        time.sleep(5)
