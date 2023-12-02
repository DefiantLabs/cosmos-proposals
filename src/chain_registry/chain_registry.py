import requests
from fs.zipfs import ZipFS
import io
import json
from .chain import Chain
from logging import INFO
from log import get_configured_logger
class ChainRegistry:

    archive = None

    def __init__(self, zip_url="https://github.com/cosmos/chain-registry/archive/refs/heads/master.zip", zip_location=None, log_level=INFO, rest_overides={}):
        self.zip_url = zip_url
        self.loaded = False
        self.archive_contents = None
        self.zip_location = zip_location
        self.log_level = log_level
        self.logger = get_configured_logger(__name__, self.log_level, "")

        self.rest_overides = rest_overides

        self.mainnets = {}
        self.testnets = {}
        self.devnets = {}
        self.unknown = {}

        self.load()
        self.extract()

    def load(self):

        if ChainRegistry.archive is not None:
            self.logger.debug("Using static chain registry archive")
            self.loaded = True
            return

        if self.zip_location:
            self.logger.debug("Loading chain registry from local zip file")
            ChainRegistry.archive = open(self.zip_location, "rb")
            self.loaded = True
            return

        self.logger.debug("Loading chain registry from url")
        resp = requests.get(self.zip_url, stream=True)

        if resp.status_code != 200:
            raise Exception(f"Unable to load chain registry from url {self.zip_url}")
        
        self.loaded = True
        ChainRegistry.archive = io.BytesIO(resp.content)
        self.logger.debug("Chain registry loaded")

    def extract(self):
        self.logger.debug("Extracting chain registry")
        if not self.loaded:
            self.load()

        self.archive = ZipFS(ChainRegistry.archive)

        mainnets = {}
        testnets = {}
        devnets = {}
        unknown = {}
        for path in self.archive.walk.files(filter=['chain.json'], exclude_dirs=["*template*"]):
            chain = json.load(self.archive.openbin(path))
            chain_path = path.split("/")[-2]

            rest_overides = []

            if chain["chain_id"] in self.rest_overides:
                rest_overides = self.rest_overides[chain["chain_id"]]

            # can chains have other statuses that are okay?
            if chain["status"] not in ["live"]:
                continue
            try:
                new_chain = Chain(chain, self.log_level, rest_overides=rest_overides)
                if chain["network_type"] == "mainnet":
                    mainnets[chain_path] = new_chain
                elif chain["network_type"] == "testnet":
                    testnets[chain_path] = new_chain
                elif chain["network_type"] == "devnet":
                    devnets[chain_path] = new_chain
                else:
                    unknown[chain_path] = new_chain
            except:
                self.logger.error(f"Unable to extract chain information for {chain_path}")
                continue

        self.mainnets = mainnets
        self.testnets = testnets
        self.devnets = devnets
        self.unknown = unknown

        self.logger.debug("Chain registry extracted")

    def get_chain(self, chain):
        chain_entry = self.get_chain_by_registry_name(chain)
        if chain_entry is not None:
            return chain_entry
        else:
            chain_entry = self.search_for_chain_by_chain_id(chain)
            if chain_entry is not None:
                return chain_entry
            raise Exception(f"Chain {chain} not found in registry")

    def get_chain_by_registry_name(self, chain):
        if chain in self.mainnets:
            return self.mainnets[chain]
        elif chain in self.testnets:
            return self.testnets[chain]
        elif chain in self.devnets:
            return self.devnets[chain]
        elif chain in self.unknown:
            return self.unknown[chain]
        return None

    def search_for_chain_by_chain_id(self, chain):
        for chain_entry in self.mainnets.values():
            if chain_entry.chain_id == chain:
                return chain_entry
        for chain_entry in self.testnets.values():
            if chain_entry.chain_id == chain:
                return chain_entry
        for chain_entry in self.devnets.values():
            if chain_entry.chain_id == chain:
                return chain_entry
        for chain_entry in self.unknown.values():
            if chain_entry.chain_id == chain:
                return chain_entry
        return None
