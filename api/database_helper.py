import os
import json

MONGODB_URL = os.environ.get('MONGODB_URL')
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'voice_ai_support')

class InMemoryDatabase:
    def __init__(self):
        self.conversations = {}
    
    def insert_one(self, document):
        conv_id = document.get("conversation_id")
        self.conversations[conv_id] = document
        return type('obj', (), {'inserted_id': conv_id})()
    
    def find_one(self, query):
        for conv in self.conversations.values():
            if all(conv.get(k) == v for k, v in query.items()):
                return conv.copy()
        return None
    
    def update_one(self, query, update):
        conv_id = query.get("conversation_id")
        if conv_id and conv_id in self.conversations:
            conv = self.conversations[conv_id]
            if "$set" in update:
                conv.update(update["$set"])
            if "$push" in update:
                for key, value in update["$push"].items():
                    if key not in conv:
                        conv[key] = []
                    conv[key].append(value)
            return type('obj', (), {'modified_count': 1})()
        return type('obj', (), {'modified_count': 0})()
    
    def ping(self):
        return True

class MongoDatabase:
    def __init__(self, db):
        self.conversations = db["conversations"]
    
    def insert_one(self, document):
        result = self.conversations.insert_one(document)
        return type('obj', (), {'inserted_id': result.inserted_id})()
    
    def find_one(self, query):
        return self.conversations.find_one(query)
    
    def update_one(self, query, update):
        result = self.conversations.update_one(query, update)
        return type('obj', (), {'modified_count': result.modified_count})()
    
    def ping(self):
        try:
            self.conversations.find_one({}, {"_id": 1})
            return True
        except Exception:
            return False

def init_db():
    if MONGODB_URL:
        try:
            from pymongo import MongoClient
            client = MongoClient(MONGODB_URL, serverSelectionTimeoutMS=5000)
            client.admin.command('ping')
            mongo_db = client[DATABASE_NAME]
            print(f"Connected to MongoDB Atlas: {DATABASE_NAME}")
            return MongoDatabase(mongo_db)
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            print("Using In-Memory Database fallback")
    
    return InMemoryDatabase()
