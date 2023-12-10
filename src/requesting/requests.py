from chain_registry import Chain
from mongo import Chain as MongoChain
from .constants import V1_REQUEST_METHOD, V1BETA1_REQUEST_METHOD
from .custom.neutron import get_neutron_active_proposals

def get_active_proposals(
    chain_name: str, chain_registry_object: Chain, chain_object: MongoChain
):
    if chain_registry_object.chain_id in CHAINS_TO_REQUEST_MAP:
        return CHAINS_TO_REQUEST_MAP[chain_registry_object.chain_id](
            chain_name, chain_registry_object, chain_object
        )
    else:
        return CHAINS_TO_REQUEST_MAP["default_fn"](
            chain_name, chain_registry_object, chain_object
        )

# This is the default proposal request function. It will be used for all chains that do not have a custom request function.
# It does the following:
# 1. Attempt to get the active proposals from the chain entry using the Gov v1 endpoint
# 2. If that fails, attempt to get the active proposals from the chain entry using the Gov v1beta1 endpoint
# 3. If that fails, return an error
def get_chain_active_proposals(
    chain_name: str, chain_registry_entry: Chain, chain_object: MongoChain
):
    try:
        return {
            "error": None,
            "active_proposals": chain_registry_entry.get_active_proposals_v1(),
            "chain_name": chain_name,
            "chain_object": chain_object,
            "chain_registry_entry": chain_registry_entry,
            "request_method": V1_REQUEST_METHOD
        }
    except Exception as e:
        try:
            return {
                "error": None,
                "active_proposals": chain_registry_entry.get_active_proposals_v1beta1(),
                "chain_name": chain_name,
                "chain_object": chain_object,
                "chain_registry_entry": chain_registry_entry,
                "request_method": V1BETA1_REQUEST_METHOD
            }
        except Exception as e:
            return {
                "error": e,
                "active_proposals": None,
                "chain_name": chain_name,
                "chain_object": chain_object,
                "chain_registry_entry": chain_registry_entry,
            }

CHAINS_TO_REQUEST_MAP = {"default_fn": get_chain_active_proposals, "neutron-1": get_neutron_active_proposals}
