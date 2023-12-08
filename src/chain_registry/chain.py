
import requests
import os
from concurrent.futures import ThreadPoolExecutor
import random

from log import get_configured_logger
from logging import INFO

import semantic_version
import re

V_SEMANTIC_VERSION_PATTERN = re.compile(r"(v\d+(?:\.\d+){0,2})")
AT_SEMANTIC_VERSION_PATTERN = re.compile(r"(@\d+(?:\.\d+){0,2})")
NO_V_NO_AT_SEMANTIC_VERSION_PATTERN = re.compile(r"(\d+(?:\.\d+){0,2})")

# TODO: to package this properly, we need to pass this as a param instead
num_workers = int(os.environ.get("NUM_WORKERS", 10))

requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

class Chain():
    def __init__(self, chain_data, log_level=INFO, default_explorer="mintscan", rest_overides=[]):
        self.chain_data = chain_data

        self.chain_id = chain_data["chain_id"]
        self.logger = get_configured_logger(__name__ + f" ({self.chain_id})", log_level, "")

        self.rpc_servers = list(map(lambda x: x["address"], chain_data["apis"]["rpc"]))
        self.rest_servers = list(map(lambda x: x["address"], chain_data["apis"]["rest"]))
        self.explorers = chain_data.get("explorers", [])
        self.default_explorer = default_explorer
        self.pretty_name = ""

        self.rest_overides = rest_overides

        self.cosmos_sdk_version_string = chain_data.get("codebase", {}).get("cosmos_sdk_version", "")

        if self.cosmos_sdk_version_string == "":
            self.cosmos_sdk_version_string = self.parse_latest_version_by_block_height(chain_data.get("codebase", {}).get("versions", [])).get("cosmos_sdk_version", "")

        # This slows down chain registry instantiation to a crawl, but it the only real way
        # to get (mostly) full coverage of the cosmos sdk version string since many chains don't store this in the registry.
        # Sometimes the node_info endpoint is also wrong due to:
        #
        # 1. The node_info endpoint not being available
        # 2. The node_info endpoint application_version.cosmos_sdk_version being wrong due to Go mod replace statements (we would need to pull the replace statements out of build_deps and parse that)
        # if self.cosmos_sdk_version_string == "":
        #     try:
        #         resp = self.get_node_info()
        #     except:
        #         resp = None
            
        #     if resp is not None:
        #         self.cosmos_sdk_version_string = resp.get("application_version", {}).get("cosmos_sdk_version", "")


        self.cosmos_sdk_version = self.parse_cosmos_sdk_versions_string(self.cosmos_sdk_version_string)

        if self.cosmos_sdk_version is None:
            self.logger.warning("Unable to parse cosmos sdk version for chain %s from string %s", self.chain_id, self.cosmos_sdk_version_string)

        if "pretty_name" in chain_data:
            self.pretty_name = chain_data["pretty_name"]
        elif "chain_name" in chain_data:
            self.pretty_name = chain_data["chain_name"]
        else:
            self.pretty_name = self.chain_id
        self.logger.debug("Initialized chain %s with RPC servers %s and REST servers %s", self.chain_id, self.rpc_servers, self.rest_servers)

    def parse_latest_version_by_block_height(self, codebase_versions):
        latest_version = {}
        latest_block_height = 0

        for version in codebase_versions:
            if "height" in version and version["height"] > latest_block_height:
                latest_version = version
                latest_block_height = version["height"]
        
        return latest_version

    def parse_cosmos_sdk_versions_string(self, version_string):

        if version_string == "":
            return None
        
        pattern_matches = V_SEMANTIC_VERSION_PATTERN.findall(version_string)

        if len(pattern_matches) == 0:
            pattern_matches = AT_SEMANTIC_VERSION_PATTERN.findall(version_string)

        if len(pattern_matches) == 0:
            pattern_matches = NO_V_NO_AT_SEMANTIC_VERSION_PATTERN.findall(version_string)
        
        if len(pattern_matches) == 0:
            return None
        
        for match in pattern_matches:
            match = match.replace("v", "")
            match = match.replace("@", "")

            if len(match.split(".")) == 1:
                match += ".0.0"
            elif len(match.split(".")) == 2:
                match += ".0"
            
            try:
                semver = semantic_version.Version(match)
                return semver
            except Exception as err:
                print(f"Error parsing version match {err}")

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
            response = requests.get(f"{endpoint}/cosmos/gov/v1beta1/proposals?proposal_status=2", timeout=3, verify=False)
            if response.status_code == 200:
                self.logger.debug("Chain %s endpoint %s is healthy from /cosmos/gov/v1beta1/proposals request", self.chain_id, endpoint)
                return True
        except:
            self.logger.debug("Chain %s endpoint %s is unhealthy from error", self.chain_id, endpoint)
            return False
        self.logger.debug("Chain %s endpoint %s is unhealthy due to error responses", self.chain_id, endpoint)
        return False
        
    def get_explorer(self, explorer_name=None):

        for explorer in self.explorers:
            if explorer_name is not None and explorer["kind"] == explorer_name:
                return explorer
            elif explorer["kind"] == self.default_explorer:
                return explorer
        return None
        
    def get_active_proposals(self):
        resp = None

        if len(self.rest_overides) == 0:
            healthy_endpoints = self.get_healthy_rest_servers()
            random.shuffle(healthy_endpoints)
        else:
            self.logger.debug("Rest endpoints are overriden for chain %s with values %s", self.chain_id, self.rest_overides)
            healthy_endpoints = self.rest_overides

        self.logger.debug("Attempting proposal request for chain %s with %d healthy endpoints", self.chain_id, len(healthy_endpoints))
        for endpoint in healthy_endpoints:
            self.logger.debug("Attempting proposal request for chain %s at %s", self.chain_id, endpoint)
            try:
                response = requests.get(
                    f"{endpoint}/cosmos/gov/v1beta1/proposals?proposal_status=2",
                    verify=False,
                    timeout=10
                )
            except Exception as e:
                self.logger.debug("Proposal request failed for chain %s at %s: %s", self.chain_id, endpoint, e)
                continue
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

    def get_node_info(self):
        resp = None

        if len(self.rest_overides) == 0:
            healthy_endpoints = self.get_healthy_rest_servers()
            random.shuffle(healthy_endpoints)
        else:
            self.logger.debug("Rest endpoints are overriden for chain %s with values %s", self.chain_id, self.rest_overides)
            healthy_endpoints = self.rest_overides

        self.logger.debug("Attempting node_info request for chain %s with %d healthy endpoints", self.chain_id, len(healthy_endpoints))
        for endpoint in healthy_endpoints:
            self.logger.debug("Attempting node_info request for chain %s at %s", self.chain_id, endpoint)
            try:
                response = requests.get(
                    f"{endpoint}/node_info",
                    verify=False,
                    timeout=10
                )
            except Exception as e:
                self.logger.debug("Node_info request failed for chain %s at %s: %s", self.chain_id, endpoint, e)
                continue
            if response.status_code == 200:
                resp = response
                break
            else:
                try:
                    response.raise_for_status()
                except Exception as e:
                    self.logger.debug("Node_info request failed for chain %s at %s: %s", self.chain_id, endpoint, e)
                    resp = None

        if resp is None:
            raise Exception(f"{self.chain_id}: Error getting node_info after trying all healthy endpoints")
        self.logger.debug("Node_info request succeeded for chain %s", self.chain_id)
        return resp.json()