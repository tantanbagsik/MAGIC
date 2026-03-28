import os
import httpx

LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'groq')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')
OLLAMA_URL = os.environ.get('OLLAMA_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.environ.get('OLLAMA_MODEL', 'llama3.2')

SUPPORT_SYSTEM_PROMPT = """You are a helpful customer support AI assistant. 
You are friendly, professional, and helpful.
Keep responses concise and clear.
If you don't know something, say you don't know and offer to escalate to a human agent."""

def get_llm_response(message, conversation_history=None):
    provider = LLM_PROVIDER.lower() if LLM_PROVIDER else 'groq'
    
    if provider == 'ollama':
        return ollama_chat(message, conversation_history)
    elif provider == 'groq' and GROQ_API_KEY:
        return groq_chat(message, conversation_history)
    elif provider == 'openai' and OPENAI_API_KEY:
        return openai_chat(message, conversation_history)
    else:
        return "LLM not configured. Please set OLLAMA_URL, GROQ_API_KEY, or OPENAI_API_KEY in environment variables."

def build_messages(message, history=None):
    messages = [{"role": "system", "content": SUPPORT_SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})
    return messages

def groq_chat(message, history=None):
    messages = build_messages(message, history)
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
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Groq Error: {str(e)}"

def openai_chat(message, history=None):
    messages = build_messages(message, history)
    try:
        response = httpx.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 500
            },
            timeout=30.0
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]
    except Exception as e:
        return f"OpenAI Error: {str(e)}"

def ollama_chat(message, history=None):
    messages = build_messages(message, history)
    try:
        response = httpx.post(
            f"{OLLAMA_URL}/api/chat",
            json={
                "model": OLLAMA_MODEL,
                "messages": messages,
                "stream": False
            },
            timeout=60.0
        )
        data = response.json()
        return data["message"]["content"]
    except Exception as e:
        return f"Ollama Error: {str(e)}. Make sure Ollama is running at {OLLAMA_URL}"

def check_ollama_status():
    try:
        response = httpx.get(f"{OLLAMA_URL}/api/tags", timeout=5.0)
        if response.status_code == 200:
            models = response.json().get("models", [])
            return {"status": "connected", "models": [m["name"] for m in models]}
        return {"status": "error", "message": f"Status code: {response.status_code}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
