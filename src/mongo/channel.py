class Channel:

    """Represents a Slack channel in the database"""

    def __init__(self, mongo_db):
        self.collection = mongo_db.channels

    def get_channel_by_id(self, channel_id):
        return self.collection.find_one({"channel_id": channel_id})
    
    def create_channel_by_id(self, channel_id):
        self.collection.insert_one({"channel_id": channel_id})

    def find_or_create_channel_by_id(self, channel_id):
        channel = self.get_channel_by_id(channel_id)
        if channel is None:
            self.create_channel_by_id(channel_id)
            channel = self.get_channel_by_id(channel_id)
        return channel
        