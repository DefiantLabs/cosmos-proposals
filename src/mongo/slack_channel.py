from datetime import datetime

class SlackChannelObject:
    def __init__(self, collection, doc):
        self.collection = collection
        self.doc = doc
        self._id = doc["_id"]
        self.channel_id = doc["channel_id"]
        self.created_at = doc["created_at"]
        self.updated_at = doc["updated_at"]

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
        