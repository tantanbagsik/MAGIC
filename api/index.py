from flask import Flask, request, jsonify
import uuid
from datetime import datetime
import os

app = Flask(__name__)

LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'groq')
REDIS_URL = os.environ.get('REDIS_URL')
MONGODB_URL = os.environ.get('MONGODB_URL')

db = None
cache = None

def init_services():
    global db, cache
    
    try:
        from database_helper import init_db
        db = init_db()
        db_status = "mongodb" if hasattr(db, 'ping') and db.ping() else "in-memory"
        print(f"Database initialized: {db_status}")
    except Exception as e:
        print(f"Database init failed: {e}")
        db = {}
        db_status = "error"
    
    try:
        from cache_helper import get_cache
        cache = get_cache()
        cache_status = "redis" if hasattr(cache, 'ping') and cache.ping() else "in-memory"
        print(f"Cache initialized: {cache_status}")
    except Exception as e:
        print(f"Cache init failed: {e}")
        cache = {}
        cache_status = "error"

init_services()

def get_db_status():
    if db is None:
        return "not-initialized"
    try:
        if hasattr(db, 'ping'):
            return "mongodb" if db.ping() else "in-memory"
    except:
        pass
    return "in-memory"

def get_cache_status():
    if cache is None:
        return "not-initialized"
    try:
        if hasattr(cache, 'ping'):
            return "redis" if cache.ping() else "in-memory"
    except:
        pass
    return "in-memory"

@app.route('/')
def root():
    return jsonify({
        "message": "VoiceAI Support API",
        "status": "running",
        "version": "1.0.0",
        "provider": LLM_PROVIDER
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "database": get_db_status(),
        "cache": get_cache_status(),
        "llm": LLM_PROVIDER,
        "timestamp": datetime.utcnow().isoformat()
    })

@app.route('/conversations', methods=['POST'])
def create_conversation():
    if db is None:
        return jsonify({"error": "Database not initialized"}), 500
    
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
    
    try:
        if hasattr(db, 'insert_one'):
            db.insert_one(conversation)
        else:
            db[conversation_id] = conversation
    except Exception as e:
        db[conversation_id] = conversation
    
    return jsonify({"conversation_id": conversation_id})

@app.route('/conversations/<conversation_id>')
def get_conversation(conversation_id):
    if db is None:
        return jsonify({"error": "Database not initialized"}), 500
    
    cached = None
    if cache and hasattr(cache, 'get'):
        try:
            cached = cache.get(f"conversation:{conversation_id}")
        except:
            pass
    
    if cached:
        return jsonify(cached)
    
    conversation = None
    try:
        if hasattr(db, 'find_one'):
            conversation = db.find_one({"conversation_id": conversation_id})
        else:
            conversation = db.get(conversation_id)
    except:
        conversation = db.get(conversation_id) if db else None
    
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    if cache and hasattr(cache, 'set'):
        try:
            cache.set(f"conversation:{conversation_id}", conversation, ttl=3600)
        except:
            pass
    
    return jsonify(conversation)

@app.route('/conversations/<conversation_id>/text-message', methods=['POST'])
def text_message(conversation_id):
    if db is None:
        return jsonify({"error": "Database not initialized"}), 500
    
    data = request.get_json()
    message = data.get('message', '')
    
    conversation = None
    try:
        if hasattr(db, 'find_one'):
            conversation = db.find_one({"conversation_id": conversation_id})
        else:
            conversation = db.get(conversation_id)
    except:
        conversation = db.get(conversation_id) if db else None
    
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    conversation_history = [
        {"role": msg["role"], "content": msg["content"]} 
        for msg in conversation.get("messages", [])
    ]
    
    try:
        from llm_helper import get_llm_response
        ai_response = get_llm_response(message, conversation_history)
    except Exception as e:
        ai_response = f"LLM Error: {str(e)}"
    
    now = datetime.utcnow().isoformat()
    conversation.setdefault("messages", []).extend([
        {"role": "user", "content": message, "created_at": now},
        {"role": "assistant", "content": ai_response, "created_at": now}
    ])
    conversation["updated_at"] = now
    
    try:
        if hasattr(db, 'update_one'):
            db.update_one(
                {"conversation_id": conversation_id},
                {"$set": {"messages": conversation["messages"], "updated_at": now}}
            )
    except:
        pass
    
    if cache and hasattr(cache, 'set'):
        try:
            cache.set(f"conversation:{conversation_id}", conversation, ttl=3600)
        except:
            pass
    
    return jsonify({"user_message": message, "ai_response": ai_response})

@app.route('/conversations/<conversation_id>/voice-message', methods=['POST'])
def voice_message(conversation_id):
    if db is None:
        return jsonify({"error": "Database not initialized"}), 500
    
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    
    conversation = None
    try:
        if hasattr(db, 'find_one'):
            conversation = db.find_one({"conversation_id": conversation_id})
        else:
            conversation = db.get(conversation_id)
    except:
        conversation = db.get(conversation_id) if db else None
    
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    
    user_message = "[Voice message - STT processing]"
    conversation_history = [
        {"role": msg["role"], "content": msg["content"]} 
        for msg in conversation.get("messages", [])
    ]
    
    try:
        from llm_helper import get_llm_response
        ai_response = get_llm_response(user_message, conversation_history)
    except Exception as e:
        ai_response = f"LLM Error: {str(e)}"
    
    now = datetime.utcnow().isoformat()
    conversation.setdefault("messages", []).extend([
        {"role": "user", "content": user_message, "created_at": now},
        {"role": "assistant", "content": ai_response, "created_at": now}
    ])
    conversation["updated_at"] = now
    
    try:
        if hasattr(db, 'update_one'):
            db.update_one(
                {"conversation_id": conversation_id},
                {"$set": {"messages": conversation["messages"], "updated_at": now}}
            )
    except:
        pass
    
    return jsonify({"user_message": user_message, "ai_response": ai_response})

@app.route('/llm-status')
def llm_status():
    try:
        from llm_helper import check_ollama_status, LLM_PROVIDER, OLLAMA_URL, OLLAMA_MODEL
        if LLM_PROVIDER == 'ollama':
            return jsonify(check_ollama_status())
        return jsonify({
            "provider": LLM_PROVIDER,
            "status": "using external API",
            "url": OLLAMA_URL if LLM_PROVIDER == 'ollama' else "groq/openai"
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

handler = app
