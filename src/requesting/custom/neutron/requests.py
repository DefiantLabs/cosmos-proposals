from .constants import BASE_LIMIT, COSMWASM_CONTRACT_ENDPOINT, NEUTRON_SINGLE_PROPOSAL_CONTRACT_ADDRESS, SINGLE_PROPOSAL_ACTIVE_STATUS
from chain_registry import Chain
from mongo import Chain as MongoChain
import requests
import base64
from requesting.constants import CUSTOM_REQUEST_METHOD
import json

def get_neutron_active_proposals(
    chain_name: str, chain_registry_object: Chain, chain_object: MongoChain
):
    for rest_server in chain_registry_object.get_rest_servers():
        proposals = {}
        try:
            start_after = None
            while True:
                proposal_page = request_single_proposal_active_proposals(
                    rest_server, BASE_LIMIT, start_after=start_after
                )
                if len(proposal_page) == 0:
                    break

                proposals.update(
                    {
                        proposal["id"]: proposal
                        for proposal in proposal_page
                    }
                )

                start_after = proposal_page[-1]["id"]
        except Exception as e:
            return {
                "error": e,
                "active_proposals": None,
                "chain_name": chain_name,
                "chain_object": chain_object,
                "chain_registry_entry": chain_registry_object,
            }
        return {
            "error": None,
            "active_proposals": {"proposals": filter_neutron_single_proposal_active_proposals(proposals.values())},
            "chain_name": chain_name,
            "chain_object": chain_object,
            "chain_registry_entry": chain_registry_object,
            "request_method": CUSTOM_REQUEST_METHOD,
        }

# The neutron CosmWasm Single Proposal is queried like so:
# 1. Get the contract address for the Neutron Single Proposal
# 2. Query the contract address with the following data:
# {
#   "list_proposals": {
#     "limit": <int>, //num to return in response
#     "start_after": <int> //pagination start
#   }
# }
def request_single_proposal_active_proposals(server, limit, start_after=None):
    json_data = {"list_proposals": {"limit": limit}}

    if start_after is not None:
        json_data["list_proposals"]["start_after"] = start_after

    base64_json_data = base64.b64encode(json.dumps(json_data).encode("utf-8"))

    response = requests.get(
        server
        + COSMWASM_CONTRACT_ENDPOINT.format(
            address=NEUTRON_SINGLE_PROPOSAL_CONTRACT_ADDRESS,
            query_data=base64_json_data.decode("utf-8"),
        )
    )

    response.raise_for_status()

    data = response.json()

    return data["data"]["proposals"]


def filter_neutron_single_proposal_active_proposals(proposals):
    return [
        proposal
        for proposal in proposals
        if proposal["proposal"]["status"] == SINGLE_PROPOSAL_ACTIVE_STATUS
    ]