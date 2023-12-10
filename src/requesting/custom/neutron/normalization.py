import datetime

def normalize_neutron_active_proposal(proposal):
    return {
        "proposal_id": proposal["id"],
        "title": proposal["proposal"].get("title", ""),
        "description": proposal["proposal"].get("description", ""),
        "submit_time": datetime.datetime.now().strftime(
            "%Y-%m-%dT%H:%M:%S"
        ),  # Neutron does not have a submit time, so we use the current time to fake it. Its currently unused in the application anyway, may be removed later.
        "type": "Neutron Single Proposal",
    }