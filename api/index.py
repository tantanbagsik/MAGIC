from flask import Flask, request, jsonify
import uuid
from datetime import datetime
import os
import httpx
import json

app = Flask(__name__)

LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'groq')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2')
REDIS_URL = os.environ.get('REDIS_URL')
MONGODB_URL = os.environ.get('MONGODB_URL')
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'voice_ai_support')

SUPPORT_SYSTEM_PROMPT = """You are a helpful customer support AI assistant. 
You are friendly, professional, and helpful.
Keep responses concise and clear."""

db = {}
cache = {}

def init_database():
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
    return InMemoryDB()

def init_cache():
    if REDIS_URL:
        try:
            import redis
            client = redis.from_url(REDIS_URL, decode_responses=True)
            client.ping()
            print("Connected to Redis")
            return RedisCache(client)
        except Exception as e:
            print(f"Redis connection failed: {e}")
    return InMemoryCache()

class InMemoryDB:
    def insert_one(self, document):
        conv_id = document.get("conversation_id")
        db[conv_id] = document
    def find_one(self, query):
        for conv in db.values():
            if all(conv.get(k) == v for k, v in query.items()):
                return conv.copy()
        return None
    def update_one(self, query, update):
        conv_id = query.get("conversation_id")
        if conv_id and conv_id in db:
            conv = db[conv_id]
            if "$set" in update:
                conv.update(update["$set"])
            if "$push" in update:
                for key, value in update["$push"].items():
                    conv.setdefault(key, []).append(value)
    def ping(self):
        return True

class MongoDatabase:
    def __init__(self, mongo_db):
        self.conversations = mongo_db["conversations"]
    def insert_one(self, document):
        self.conversations.insert_one(document)
    def find_one(self, query):
        return self.conversations.find_one(query)
    def update_one(self, query, update):
        self.conversations.update_one(query, update)
    def ping(self):
        try:
            self.conversations.find_one({}, {"_id": 1})
            return True
        except:
            return False

class InMemoryCache:
    def __init__(self):
        self.data = {}
    def get(self, key):
        return self.data.get(key)
    def set(self, key, value, ttl=3600):
        self.data[key] = value
    def delete(self, key):
        if key in self.data:
            del self.data[key]
    def ping(self):
        return True

class RedisCache:
    def __init__(self, client):
        self.client = client
    def get(self, key):
        data = self.client.get(key)
        if data:
            return json.loads(data)
        return None
    def set(self, key, value, ttl=3600):
        self.client.setex(key, ttl, json.dumps(value))
    def delete(self, key):
        self.client.delete(key)
    def ping(self):
        return self.client.ping()

database = init_database()
cache = init_cache()

def get_llm_response(message, conversation_history=None):
    messages = [{"role": "system", "content": SUPPORT_SYSTEM_PROMPT}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": message})
    
    provider = LLM_PROVIDER.lower() if LLM_PROVIDER else 'groq'
    
    if provider == 'ollama':
        try:
            response = httpx.post(
                f"{OLLAMA_URL}/api/chat",
                json={"model": OLLAMA_MODEL, "messages": messages, "stream": False},
                timeout=60.0
            )
            return response.json()["message"]["content"]
        except Exception as e:
            return f"Ollama Error: {str(e)}"
    
    elif provider == 'groq' and GROQ_API_KEY:
        try:
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": "llama-3.1-8b-instant", "messages": messages, "temperature": 0.7, "max_tokens": 500},
                timeout=30.0
            )
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"Groq Error: {str(e)}"
    
    elif provider == 'openai' and OPENAI_API_KEY:
        try:
            response = httpx.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {OPENAI_API_KEY}", "Content-Type": "application/json"},
                json={"model": "gpt-3.5-turbo", "messages": messages, "temperature": 0.7, "max_tokens": 500},
                timeout=30.0
            )
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"OpenAI Error: {str(e)}"
    
    return "LLM not configured. Set GROQ_API_KEY, OPENAI_API_KEY, or OLLAMA_URL."

@app.route('/')
def root():
    return jsonify({"message": "VoiceAI Support API", "status": "running", "version": "1.0.0"})

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "database": "mongodb" if isinstance(database, MongoDatabase) else "in-memory",
        "cache": "redis" if isinstance(cache, RedisCache) else "in-memory",
        "llm": LLM_PROVIDER,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/conversations', methods=['POST'])
def create_conversation():
    data = request.get_json() or {}
    conversation_id = str(uuid.uuid4())
    conversation = {
        "conversation_id": conversation_id,
        "customer_id": data.get('customer_id'),
        "status": "active",
        "messages": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    database.insert_one(conversation)
    return jsonify({"conversation_id": conversation_id})

@app.route('/conversations/<conversation_id>')
def get_conversation(conversation_id):
    cached = cache.get(f"conversation:{conversation_id}")
    if cached:
        return jsonify(cached)
    conversation = database.find_one({"conversation_id": conversation_id})
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    cache.set(f"conversation:{conversation_id}", conversation, ttl=3600)
    return jsonify(conversation)

@app.route('/conversations/<conversation_id>/text-message', methods=['POST'])
def text_message(conversation_id):
    data = request.get_json()
    message = data.get('message', '')
    conversation = database.find_one({"conversation_id": conversation_id})
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    conversation_history = [{"role": msg["role"], "content": msg["content"]} for msg in conversation.get("messages", [])]
    ai_response = get_llm_response(message, conversation_history)
    
    now = datetime.utcnow().isoformat()
    conversation.setdefault("messages", []).extend([
        {"role": "user", "content": message, "created_at": now},
        {"role": "assistant", "content": ai_response, "created_at": now}
    ])
    conversation["updated_at"] = now
    
    database.update_one({"conversation_id": conversation_id}, {"$set": {"messages": conversation["messages"], "updated_at": now}})
    cache.set(f"conversation:{conversation_id}", conversation, ttl=3600)
    
    return jsonify({"user_message": message, "ai_response": ai_response})

@app.route('/conversations/<conversation_id>/voice-message', methods=['POST'])
def voice_message(conversation_id):
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    conversation = database.find_one({"conversation_id": conversation_id})
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    user_message = "[Voice message - STT processing]"
    conversation_history = [{"role": msg["role"], "content": msg["content"]} for msg in conversation.get("messages", [])]
    ai_response = get_llm_response(user_message, conversation_history)
    
    now = datetime.utcnow().isoformat()
    conversation.setdefault("messages", []).extend([
        {"role": "user", "content": user_message, "created_at": now},
        {"role": "assistant", "content": ai_response, "created_at": now}
    ])
    conversation["updated_at"] = now
    
    database.update_one({"conversation_id": conversation_id}, {"$set": {"messages": conversation["messages"], "updated_at": now}})
    
    return jsonify({"user_message": user_message, "ai_response": ai_response})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

handler = app
