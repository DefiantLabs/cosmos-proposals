from cosmos.gov.v1beta1.proposals_pb2 import TextProposal, SoftwareUpgradeProposal, MsgExecuteContract, CommunityPoolSpendProposal, ParameterChangeProposal, ClientUpdateProposal

class ProposalRegistry():
    def __init__(self):
        self.registry = {
            "/cosmos.gov.v1beta1.TextProposal": TextProposal,
            "/cosmos.upgrade.v1beta1.SoftwareUpgradeProposal": SoftwareUpgradeProposal,
            "/cosmwasm.wasm.v1.MsgExecuteContract": MsgExecuteContract,
            "/cosmos.distribution.v1beta1.CommunityPoolSpendProposal": CommunityPoolSpendProposal,
            "/cosmos.params.v1beta1.ParameterChangeProposal": ParameterChangeProposal,
            "/ibc.core.client.v1.ClientUpdateProposal": ClientUpdateProposal
        }

    def get_proposal(self, type_url):
        return self.registry[type_url]

    def get_all_proposals(self):
        return self.registry.values()