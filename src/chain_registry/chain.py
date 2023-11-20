
import requests
import os
from concurrent.futures import ThreadPoolExecutor

num_workers = int(os.environ.get("NUM_WORKERS", 10))

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

class Chain():
    def __init__(self, chain_data):
        self.chain_data = chain_data

        self.chain_id = chain_data["chain_id"]
        self.rpc_servers = map(lambda x: x["address"], chain_data["apis"]["rpc"])
        self.rest_servers = map(lambda x: x["address"], chain_data["apis"]["rest"])
    
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
            response = requests.get(f"{endpoint}/health", timeout=1, verify=False)
            # some chains dont implement the /health endpoint. Should we just skip /health and go directly to the below?
            if response.status_code == 501:
                response = requests.get(
                    f"{endpoint}/cosmos/gov/v1beta1/proposals?proposal_status=2",
                    timeout=1,
                    verify=False,
                )
            return response.status_code == 200
        except:
            return False