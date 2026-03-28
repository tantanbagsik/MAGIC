from flask import Flask, request, jsonify
import uuid
from datetime import datetime
import os

app = Flask(__name__)

db = {}
cache = {}

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
        "cache": "in-memory",
        "llm": "configured",
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
        from _llm import get_llm_response
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
        from _llm import get_llm_response
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
