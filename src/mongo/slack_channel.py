from datetime import datetime

class SlackChannelObject:
    def __init__(self, collection, doc):
        self.collection = collection
        self.doc = doc
        self._id = doc["_id"]
        self.channel_id = doc["channel_id"]
        self.created_at = doc["created_at"]
        self.updated_at = doc["updated_at"]

        if "proposals_notified" in doc:
            self.proposals_notified = doc["proposals_notified"]
        else:
            self.proposals_notified = {}

    def is_proposal_notified(self, proposal_id):
        return str(proposal_id) in self.proposals_notified

    def set_proposal_notified(self, proposal_id):
        self.proposals_notified[str(proposal_id)] = True
        time_now = datetime.utcnow()
        self.collection.update_one({"_id": self._id}, {"$set": {"updated_at": time_now, "proposals_notified": self.proposals_notified}})

class SlackChannel:

    """Represents a Slack channel in the database"""

    def __init__(self, mongo_db):
        self.collection = mongo_db.channels

    def get_channel_by_id(self, channel_id):
        obj = self.collection.find_one({"channel_id": channel_id})

        if obj is None:
            return None
        else:
            return SlackChannelObject(self.collection, obj)

    def create_channel_by_id(self, channel_id):
        time_now = datetime.utcnow()
        self.collection.insert_one({"channel_id": channel_id, "created_at": time_now, "updated_at": time_now})

    def find_or_create_channel_by_id(self, channel_id):
        channel = self.get_channel_by_id(channel_id)
        if channel is None:
            self.create_channel_by_id(channel_id)
            return self.get_channel_by_id(channel_id)
        else:
            return channel

