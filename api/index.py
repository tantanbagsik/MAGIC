from flask import Flask, request, jsonify
import uuid
from datetime import datetime
import os
import httpx

app = Flask(__name__)

LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'groq')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

SUPPORT_SYSTEM_PROMPT = """You are a helpful customer support AI assistant. 
You are friendly, professional, and helpful.
Keep responses concise and clear."""

def get_llm_response(message, conversation_history=None):
    messages = [{"role": "system", "content": SUPPORT_SYSTEM_PROMPT}]
    if conversation_history:
        messages.extend(conversation_history)
    messages.append({"role": "user", "content": message})
    
    if LLM_PROVIDER == 'groq' and GROQ_API_KEY:
        try:
            response = httpx.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": messages,
                    "temperature": 0.7,
                    "max_tokens": 500
                },
                timeout=30.0
            )
            return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            return f"LLM Error: {str(e)}"
    return "LLM not configured. Set GROQ_API_KEY in Vercel environment variables."

db = {}

try:
    from cache_helper import get_cache
    cache = get_cache()
    cache_status = "connected" if cache.ping() else "in-memory"
except Exception:
    cache = {}
    cache_status = "in-memory"

@app.route('/')
def root():
    return jsonify({
        "message": "VoiceAI Support API",
        "status": "running",
        "version": "1.0.0"
    })

@app.route('/health')
def health():
    return jsonify({
        "status": "healthy",
        "database": "in-memory",
        "cache": cache_status,
        "llm": "groq" if GROQ_API_KEY else "not-configured",
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
    db[conversation_id] = conversation
    return jsonify({"conversation_id": conversation_id})

@app.route('/conversations/<conversation_id>')
def get_conversation(conversation_id):
    cached = cache.get(f"conversation:{conversation_id}") if isinstance(cache, dict) == False else None
    if cached:
        return jsonify(cached)
    conversation = db.get(conversation_id)
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    return jsonify(conversation)

@app.route('/conversations/<conversation_id>/text-message', methods=['POST'])
def text_message(conversation_id):
    data = request.get_json()
    message = data.get('message', '')
    conversation = db.get(conversation_id)
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    conversation_history = [{"role": msg["role"], "content": msg["content"]} for msg in conversation.get("messages", [])]
    try:
        ai_response = get_llm_response(message, conversation_history)
    except Exception as e:
        ai_response = f"LLM Error: {str(e)}"
    now = datetime.utcnow().isoformat()
    conversation.setdefault("messages", []).extend([
        {"role": "user", "content": message, "created_at": now},
        {"role": "assistant", "content": ai_response, "created_at": now}
    ])
    conversation["updated_at"] = now
    return jsonify({"user_message": message, "ai_response": ai_response})

@app.route('/conversations/<conversation_id>/voice-message', methods=['POST'])
def voice_message(conversation_id):
    if 'audio' not in request.files:
        return jsonify({"error": "No audio file provided"}), 400
    conversation = db.get(conversation_id)
    if not conversation:
        return jsonify({"error": "Conversation not found"}), 404
    user_message = "[Voice message - STT processing]"
    conversation_history = [{"role": msg["role"], "content": msg["content"]} for msg in conversation.get("messages", [])]
    try:
        ai_response = get_llm_response(user_message, conversation_history)
    except Exception as e:
        ai_response = f"LLM Error: {str(e)}"
    now = datetime.utcnow().isoformat()
    conversation.setdefault("messages", []).extend([
        {"role": "user", "content": user_message, "created_at": now},
        {"role": "assistant", "content": ai_response, "created_at": now}
    ])
    conversation["updated_at"] = now
    return jsonify({"user_message": user_message, "ai_response": ai_response})

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

handler = app
