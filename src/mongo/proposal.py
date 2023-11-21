from datetime import datetime

class ProposalObject:
    def __init__(self, collection, doc):
        self.collection = collection
        self.doc = doc
        self._id = doc["_id"]
        self.proposal_id = doc["proposal_id"]
        self.created_at = doc["created_at"]
        self.updated_at = doc["updated_at"]
        if "submit_time" in doc:
            self.submit_time = doc["submit_time"]
        else:
            self.submit_time = None
    
    def get_proposal_submit_time(self):
        return self.submit_time

    def set_proposal_submit_time(self, submit_time):
        time_now = datetime.utcnow()
        self.collection.update_one({"_id": self._id}, {"$set": {"updated_at": time_now, "submit_time": submit_time}})
        self.submit_time = submit_time
    
    def get_or_set_proposal_submit_time(self, submit_time):
        if self.submit_time is None:
            self.set_proposal_submit_time(submit_time)
            return self.get_proposal_submit_time()
        else:
            return self.get_proposal_submit_time()

class Proposal:
    def __init__(self, mongo_db):
        self.collection = mongo_db.proposals
    
    def get_proposal_by_chain_and_id(self, chain_id, proposal_id):
        obj = self.collection.find_one({"chain_id": chain_id, "proposal_id": proposal_id})

        if obj is None:
            return None
        else:
            return ProposalObject(self.collection, obj)
    
    def create_proposal_by_chain_and_id(self, chain_id, proposal_id):
        time_now = datetime.utcnow()
        self.collection.insert_one({"chain_id": chain_id, "proposal_id": proposal_id, "created_at": time_now, "updated_at": time_now})

    def find_or_create_proposal_by_chain_and_id(self, chain_id, proposal_id):
        proposal = self.get_proposal_by_chain_and_id(chain_id, proposal_id)
        if proposal is None:
            self.create_proposal_by_chain_and_id(chain_id, proposal_id)
            return self.get_proposal_by_chain_and_id(chain_id, proposal_id)
        else:
            return proposal
        