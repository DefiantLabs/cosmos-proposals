from cosmos.gov.v1beta1.query_pb2 import QueryProposalsRequest, ProposalStatus, QueryProposalsResponse
import requests
import base64

def request_active_proposals(server):
    request = QueryProposalsRequest(proposal_status=ProposalStatus.PROPOSAL_STATUS_VOTING_PERIOD)

    request_bytes = request.SerializeToString()

    blob = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "abci_query",
        "params": {
            "path": "/cosmos.gov.v1beta1.Query/Proposals",
            "data": request_bytes.hex(),
        }
    }

    resp = requests.post(server, json=blob, timeout=5)

    resp.raise_for_status()

    data = resp.json()

    response = QueryProposalsResponse()
    
    response.ParseFromString(base64.b64decode(data["result"]["response"]["value"]))
    return response