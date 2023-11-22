
import requests
import os
from concurrent.futures import ThreadPoolExecutor
import random

from log import get_configured_logger
from logging import INFO

num_workers = int(os.environ.get("NUM_WORKERS", 10))

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

class Chain():
    def __init__(self, chain_data, log_level=INFO):
        self.chain_data = chain_data
        print(log_level)
        self.logger = get_configured_logger(__name__, log_level, "")

        self.chain_id = chain_data["chain_id"]
        self.rpc_servers = list(map(lambda x: x["address"], chain_data["apis"]["rpc"]))
        self.rest_servers = list(map(lambda x: x["address"], chain_data["apis"]["rest"]))

        self.logger.debug("Initialized chain %s with RPC servers %s and REST servers %s", self.chain_id, self.rpc_servers, self.rest_servers)
    
    def get_chain_id(self):
        return self.chain_id
    
    def get_rpc_servers(self):
        return self.rpc_servers
    
    def get_rest_servers(self):
        return self.rest_servers
    
    def get_healthy_rest_servers(self):
        return self._execute_health_check(self.get_rest_servers())
    
    def get_healthy_rpc_servers(self):
        return self._execute_health_check(self.get_rpc_servers())
    
    def _execute_health_check(self, servers):
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            healthy_endpoints = [
                server
                for server, is_healthy in executor.map(
                    lambda server: (server, self._is_endpoint_healthy(server)), servers
                )
                if is_healthy
            ]
        return healthy_endpoints

    def _is_endpoint_healthy(self, endpoint):
        try:
            response = requests.get(f"{endpoint}/node_info", timeout=3, verify=False)
            if response.status_code == 200:
                self.logger.debug("Chain %s endpoint %s is healthy from /node_info request", self.chain_id, endpoint)
                return True
            response = requests.get(f"{endpoint}/cosmos/gov/v1beta1/proposals", timeout=3, verify=False)
            if response.status_code == 200:
                self.logger.debug("Chain %s endpoint %s is healthy from /cosmos/gov/v1beta1/proposals request", self.chain_id, endpoint)
                return True
        except:
            self.logger.debug("Chain %s endpoint %s is unhealthy from error", self.chain_id, endpoint)
            return False
        self.logger.debug("Chain %s endpoint %s is unhealthy due to error responses", self.chain_id, endpoint)
        return False
        
    def get_active_proposals(self):
        resp = None
        healthy_endpoints = self.get_healthy_rest_servers()
        random.shuffle(healthy_endpoints)
        self.logger.debug("Attempting proposal request for chain %s with %d healthy endpoints", self.chain_id, len(healthy_endpoints))
        for endpoint in healthy_endpoints:
            self.logger.debug("Attempting proposal request for chain %s at %s", self.chain_id, endpoint)
            response = requests.get(
                f"{endpoint}/cosmos/gov/v1beta1/proposals?proposal_status=2",
                verify=False,
            )
            if response.status_code == 200:
                resp = response
                break
            else:
                try:
                    response.raise_for_status()
                except Exception as e:
                    self.logger.debug("Proposal request failed for chain %s at %s: %s", self.chain_id, endpoint, e)
                    resp = None

        if resp is None:
            raise Exception(f"{self.chain_id}: Error getting active proposals after trying all healthy endpoints")
        self.logger.debug("Proposal request succeeded for chain %s", self.chain_id)
        return resp.json()