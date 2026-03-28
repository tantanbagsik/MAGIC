import os
import httpx

LLM_PROVIDER = os.environ.get('LLM_PROVIDER', 'groq')
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

SUPPORT_SYSTEM_PROMPT = """You are a helpful customer support AI assistant. 
You are friendly, professional, and helpful.
Keep responses concise and clear.
If you don't know something, say you don't know and offer to escalate to a human agent."""

def get_llm_response(message, conversation_history=None):
    if LLM_PROVIDER == 'groq' and GROQ_API_KEY:
        return groq_chat(message, conversation_history)
    elif LLM_PROVIDER == 'openai' and OPENAI_API_KEY:
        return openai_chat(message, conversation_history)
    else:
        return "LLM not configured. Please set GROQ_API_KEY or OPENAI_API_KEY in Vercel environment variables."

def groq_chat(message, history=None):
    messages = [{"role": "system", "content": SUPPORT_SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})
    
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
        return f"Error: {str(e)}"

def openai_chat(message, history=None):
    messages = [{"role": "system", "content": SUPPORT_SYSTEM_PROMPT}]
    if history:
        messages.extend(history)
    messages.append({"role": "user", "content": message})
    
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
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        return f"Error: {str(e)}"
