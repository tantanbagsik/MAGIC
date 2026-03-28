import httpx
from typing import List, Dict, Optional, Any
from config import config

class LLMService:
    def __init__(self, model: Optional[str] = None):
        self.model = model or config.OLLAMA_MODEL
        self.base_url = config.OLLAMA_BASE_URL
    
    def chat(self, message: str, conversation_history: Optional[List[Dict[str, Any]]] = None) -> str:
        if not self.check_connection():
            return "I'm currently unavailable. Please ensure Ollama is running with: ollama serve && ollama pull llama3.2"
        
        messages = [{"role": "system", "content": config.SUPPORT_SYSTEM_PROMPT}]
        
        if conversation_history:
            messages.extend(conversation_history)
        
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False
        }
        
        try:
            with httpx.Client(timeout=120.0) as client:
                response = client.post(f"{self.base_url}/api/chat", json=payload)
                response.raise_for_status()
                return response.json()["message"]["content"]
        except Exception as e:
            return f"I encountered an error processing your request. Please check that Ollama is running properly. Error: {str(e)}"
    
    def check_connection(self) -> bool:
        try:
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{self.base_url}/api/tags")
                return response.status_code == 200
        except Exception:
            return False

llm_service = LLMService()
