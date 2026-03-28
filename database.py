import json
import os
from typing import Optional, Dict, Any

try:
    from motor.motor_asyncio import AsyncIOMotorClient
    from config import config
    HAS_MONGODB = True
except ImportError:
    HAS_MONGODB = False
    config = None

class MongoDatabase:
    def __init__(self):
        self.client = None
    
    async def connect(self):
        self.client = AsyncIOMotorClient(config.MONGODB_URL)
        await self.client.admin.command('ping')
        print(f"Connected to MongoDB Atlas: {config.DATABASE_NAME}")
    
    async def disconnect(self):
        if self.client:
            self.client.close()
            print("Disconnected from MongoDB Atlas")
    
    def get_collection(self, name: str):
        return self.client[config.DATABASE_NAME][name]

class FileDatabase:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(__file__), "data")
        os.makedirs(self.db_path, exist_ok=True)
        self.conversations_file = os.path.join(self.db_path, "conversations.json")
        self._load_data()
    
    def _load_data(self):
        if os.path.exists(self.conversations_file):
            try:
                with open(self.conversations_file, 'r') as f:
                    self.conversations = json.load(f)
            except Exception:
                self.conversations = {}
        else:
            self.conversations = {}
        self._save_data()
    
    def _save_data(self):
        with open(self.conversations_file, 'w') as f:
            json.dump(self.conversations, f, default=str, indent=2)
    
    async def connect(self):
        print("Using File Database (MongoDB unavailable)")
    
    async def disconnect(self):
        self._save_data()
        print("File Database saved")
    
    def get_collection(self, name: str):
        return FileCollection(self, name)

class FileCollection:
    def __init__(self, db: FileDatabase, name: str):
        self.db = db
        self.name = name
    
    async def insert_one(self, document: Dict):
        conv_id = document.get("conversation_id")
        if conv_id:
            self.db.conversations[conv_id] = document
            self.db._save_data()
        result = type('Result', (), {'inserted_id': conv_id})()
        return result
    
    async def find_one(self, query: Dict) -> Optional[Dict]:
        for conv in self.db.conversations.values():
            match = True
            for key, value in query.items():
                if conv.get(key) != value:
                    match = False
                    break
            if match:
                return conv.copy()
        return None
    
    async def update_one(self, query: Dict, update: Dict):
        conv = await self.find_one(query)
        if conv:
            conv_id = conv["conversation_id"]
            
            if "$set" in update:
                self.db.conversations[conv_id].update(update["$set"])
            
            if "$push" in update:
                for key, value in update["$push"].items():
                    if key not in self.db.conversations[conv_id]:
                        self.db.conversations[conv_id][key] = []
                    self.db.conversations[conv_id][key].append(value)
            
            self.db._save_data()
            result = type('Result', (), {'modified_count': 1})()
            return result
        result = type('Result', (), {'modified_count': 0})()
        return result

async def get_database():
    if HAS_MONGODB and config:
        mongo_db = MongoDatabase()
        try:
            await mongo_db.connect()
            return mongo_db
        except Exception as e:
            print(f"MongoDB connection failed: {e}")
            print("Falling back to file database...")
            return FileDatabase()
    return FileDatabase()

# Initialize db at module level
db = FileDatabase()
db_loaded = False

async def init_db():
    global db, db_loaded
    if not db_loaded:
        db = await get_database()
        await db.connect()
        db_loaded = True
    return db
