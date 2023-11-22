import requests
from fs.zipfs import ZipFS
import io
import json
from .chain import Chain
from logging import INFO
class ChainRegistry:

    archive = None

    def __init__(self, zip_url="https://github.com/cosmos/chain-registry/archive/refs/heads/master.zip", zip_location=None, log_level=INFO):
        self.zip_url = zip_url
        self.loaded = False
        self.archive_contents = None
        self.zip_location = zip_location
        self.log_level = log_level

        self.mainnets = {}
        self.testnets = {}
        self.devnets = {}
        self.unknown = {}

        self.load()
        self.extract()

    def load(self):

        if ChainRegistry.archive is not None:
            self.loaded = True
            return

        if self.zip_location:
            ChainRegistry.archive = open(self.zip_location, "rb")
            self.loaded = True
            return

        resp = requests.get(self.zip_url, stream=True)

        if resp.status_code != 200:
            raise Exception(f"Unable to load chain registry from url {self.zip_url}")
        
        self.loaded = True
        ChainRegistry.archive = io.BytesIO(resp.content)

    def extract(self):
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

            # can chains have other statuses that are okay?
            if chain["status"] not in ["live"]:
                continue
            try:
                if chain["network_type"] == "mainnet":
                    mainnets[chain_path] = Chain(chain, self.log_level)
                elif chain["network_type"] == "testnet":
                    testnets[chain_path] = Chain(chain, self.log_level)
                elif chain["network_type"] == "devnet":
                    devnets[chain_path] = Chain(chain, self.log_level)
                else:
                    unknown[chain_path] = Chain(chain, self.log_level)
            except:
                print(f"Unable to extract chain information for {chain_path}")
                continue

        self.mainnets = mainnets
        self.testnets = testnets
        self.devnets = devnets
        self.unknown = unknown

    def get_chain(self, chain):
        if chain in self.mainnets:
            return self.mainnets[chain]
        elif chain in self.testnets:
            return self.testnets[chain]
        elif chain in self.devnets:
            return self.devnets[chain]
        elif chain in self.unknown:
            return self.unknown[chain]
        else:
            raise Exception(f"Chain {chain} not found in registry")
