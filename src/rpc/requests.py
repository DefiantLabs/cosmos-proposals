from cosmos.gov.v1beta1.query_pb2 import QueryProposalsRequest, ProposalStatus, QueryProposalsResponse, QueryProposalRequest, QueryProposalResponse
from cosmos.gov.v1.query_pb2 import QueryProposalsRequest as QueryProposalsRequest_v1, ProposalStatus as ProposalStatus_v1, QueryProposalsResponse as QueryProposalsResponse_v1

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

def request_active_proposals_v1(server):
    request = QueryProposalsRequest_v1(proposal_status=ProposalStatus_v1.PROPOSAL_STATUS_VOTING_PERIOD)

    request_bytes = request.SerializeToString()

    blob = {
        "jsonrpc": "2.0",
        "id": 0,
        "method": "abci_query",
        "params": {
            "path": "/cosmos.gov.v1.Query/Proposals",
            "data": request_bytes.hex(),
        }
    }

    resp = requests.post(server, json=blob, timeout=5)

    resp.raise_for_status()

    data = resp.json()

    if data["result"]["response"]["code"] != 0:
        raise Exception(f"Proposals response returned error code {data['result']['response']['code']}: {data['result']['response']['log']}")

    response = QueryProposalsResponse_v1()
    
    response.ParseFromString(base64.b64decode(data["result"]["response"]["value"]))
    return response

def request_proposals_by_proposal_id(server, proposal_id):
    request = QueryProposalRequest(proposal_id=proposal_id)

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

    response = QueryProposalResponse()
    
    response.ParseFromString(base64.b64decode(data["result"]["response"]["value"]))
    return response