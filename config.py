import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGODB_URL = os.getenv("MONGODB_URL", "mongodb://localhost:27017")
    DATABASE_NAME = os.getenv("DATABASE_NAME", "voice_ai_support")
    
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2")
    
    SUPPORT_SYSTEM_PROMPT = """You are a helpful customer support AI assistant. 
    You are friendly, professional, and helpful.
    Keep responses concise and clear.
    If you don't know something, say you don't know and offer to escalate to a human agent.
    Always be polite and patient."""
    
    AUDIO_DIR = os.path.join(os.path.dirname(__file__), "audio_files")
    os.makedirs(AUDIO_DIR, exist_ok=True)

config = Config()
