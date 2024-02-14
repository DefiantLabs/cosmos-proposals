from .constants import V1_REQUEST_METHOD, V1BETA1_REQUEST_METHOD, CUSTOM_REQUEST_METHOD
from .custom.neutron import normalize_neutron_active_proposal

def normalize_proposal_response(chain_registry_entry, proposal, request_method):

    if request_method == CUSTOM_REQUEST_METHOD and chain_registry_entry.chain_id in CHAINS_TO_NORMALIZE_MAP:
        return CHAINS_TO_NORMALIZE_MAP[chain_registry_entry.chain_id](proposal)
    elif request_method != CUSTOM_REQUEST_METHOD:
        return REQUEST_METHOD_TO_NORMALIZE_MAP[request_method](proposal)
    else: 
        raise Exception(f"Chain {chain_registry_entry.chain_id} does not have a proposal data normalization function")


def normalize_v1_proposal(proposal):
    title = proposal.get("title", "")
    description = proposal.get("summary", "")

    first_message = {}
    if len(proposal["messages"]) > 0:
        first_message = proposal["messages"][0]

    if title == "" or description == "" and len(proposal["messages"]) > 0:
        if title == "":
            title = first_message.get("content", {}).get("title", "")
        if description == "":
            description = first_message.get("content", {}).get("description", "")
    return {
        "proposal_id": proposal["id"],
        "title": title,
        "description": description,
        "submit_time": proposal["submit_time"],
        "type": first_message.get("@type", ""),
        "status": proposal.get("status", ""),
    }


def normalize_v1beta1_proposal(proposal):
    return {
        "proposal_id": proposal["proposal_id"],
        "title": proposal["content"].get("title", ""),
        "description": proposal["content"].get("description", ""),
        "submit_time": proposal["submit_time"],
        "type": proposal["content"].get("@type", ""),
        "status": proposal.get("status", ""),
    }


REQUEST_METHOD_TO_NORMALIZE_MAP = {
    V1_REQUEST_METHOD: normalize_v1_proposal,
    V1BETA1_REQUEST_METHOD: normalize_v1beta1_proposal,
}

CHAINS_TO_NORMALIZE_MAP = {
    "neutron-1": normalize_neutron_active_proposal
}