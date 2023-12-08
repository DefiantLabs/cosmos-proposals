from chain_registry import ChainRegistry
import pytest

@pytest.fixture
def default_chain_registry():
    return ChainRegistry()

def test_chain_registry_instantiation(default_chain_registry):
    assert default_chain_registry is not None

# These chains are known to have bad or inconsistent semver strings either in the chain reg or in the node_info endpoint
# We skip these chains for now
semver_test_blacklist = [
   
]

def test_chain_registry_chains_have_semver(default_chain_registry):
    missing_semver_chains = []
    for chain in default_chain_registry.mainnets.values():
        if chain.chain_id in semver_test_blacklist:
            continue
        try:
            assert chain.cosmos_sdk_version
        except:
            print(f"Chain {chain.chain_id} does not have a semver version")
            missing_semver_chains.append(chain.chain_id)

    assert len(missing_semver_chains) == 0, f"Chains {missing_semver_chains} do not have semver versions"