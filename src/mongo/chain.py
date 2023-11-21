from datetime import datetime

class ChainObject:
    def __init__(self, collection, doc):
        self.collection = collection
        self.doc = doc
        self._id = doc["_id"]
        self.chain_name = doc["chain_name"]
        self.created_at = doc["created_at"]
        self.updated_at = doc["updated_at"]

class Chain:
    def __init__(self, mongo_db):
        self.collection = mongo_db.chains
    
    def get_chain_by_name(self, chain_name):
        obj = self.collection.find_one({"chain_name": chain_name})

        if obj is None:
            return None
        else:
            return ChainObject(self.collection, obj)
    
    def create_chain_by_name(self, chain_name):
        time_now = datetime.utcnow()
        self.collection.insert_one({"chain_name": chain_name, "created_at": time_now, "updated_at": time_now})

    def find_or_create_chain_by_name(self, chain_name):
        chain = self.get_chain_by_name(chain_name)
        if chain is None:
            self.create_chain_by_name(chain_name)
            return self.get_chain_by_name(chain_name)
        else:
            return chain
        