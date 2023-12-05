from rpc.requests import request_active_proposals
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

            for proposal in active_proposals.proposals:
                proposal_type = proposal.content.type_url
                proposal_data = proposal.content.value
                proposal_proto = proposal_registry.get_proposal(proposal_type)()
                proposal_proto.ParseFromString(proposal_data)
                

main()
