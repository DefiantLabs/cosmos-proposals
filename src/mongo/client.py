from pymongo import MongoClient

def get_client(uri):
    return MongoClient(uri)

def get_database(client):
    return client.cosmos_proposals