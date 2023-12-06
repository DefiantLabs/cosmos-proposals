from rpc.requests import request_active_proposals, request_proposals_by_proposal_id, request_active_proposals_v1
from chain_registry.chain_registry import ChainRegistry
import time
from cosmos.gov.v1beta1.proposals_pb2 import TextProposal, SoftwareUpgradeProposal, MsgExecuteContract
from rpc.proposal_registry import ProposalRegistry
import random
chain_registry = ChainRegistry(zip_location="./.venv/chain-registry-master.zip")

chains =  [
      "agoric",
      "akash",
      "celestia",
      "cosmoshub",
      "crescent",
      "dydx",
      "evmos",
      "injective",
      "juno",
      "nolus",
      "omniflixhub",
      "osmosis",
      "quasar",
      "sentinel",
      "stargaze"
]

def main():
    proposal_registry = ProposalRegistry()
    for chain in chains:
        rpc_servers = chain_registry.get_chain(chain).get_rpc_servers()

        print("Testing v1beta1 requests")
        if len(rpc_servers) != 0:
            print(chain)
            random.shuffle(rpc_servers)

            active_proposals = None
            for rpc_server in rpc_servers:
                try:
                    active_proposals = request_active_proposals(rpc_server)
                    break
                except:
                    print("Error with chain: " + chain + " and rpc server: " + rpc_server)
                    continue
            

        print("Testing v1 requests")
        if len(rpc_servers) != 0:
            print(chain)
            random.shuffle(rpc_servers)

            active_proposals = None
            for rpc_server in rpc_servers:
                try:
                    active_proposals = request_active_proposals_v1(rpc_server)
                    break
                except Exception as err:
                    print("Error with chain: " + chain + " and rpc server: " + rpc_server)
                    print(err)
                    continue
            
            print(active_proposals)


main()
