# Voice AI Customer Support Bot

A Python-based voice AI solution for customer support using Ollama (local LLM) and MongoDB.

## Architecture

- **STT**: OpenAI Whisper (local)
- **LLM**: Ollama (llama3.2)
- **TTS**: gTTS
- **Database**: MongoDB
- **API**: FastAPI

## Setup

### 1. Install dependencies
```bash
cd voice-ai-support
pip install -r requirements.txt
```

### 2. Start MongoDB
```bash
mongod
```

### 3. Start Ollama
```bash
ollama serve
ollama pull llama3.2
```

### 4. Run the app
```bash
uvicorn main:app --reload
```

### 5. Open frontend
Navigate to `index.html` in your browser

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Ollama connection status |
| POST | `/conversations` | Create new conversation |
| GET | `/conversations/{id}` | Get conversation |
| POST | `/conversations/{id}/voice-message` | Process voice message |
| POST | `/conversations/{id}/text-message` | Process text message |

## Example Usage

```bash
# Create conversation
curl -X POST http://localhost:8000/conversations

# Send voice message
curl -X POST -F "audio=@audio.webm" \
  http://localhost:8000/conversations/{id}/voice-message

# Send text message
curl -X POST -H "Content-Type: application/json" \
  -d '{"message": "Hello"}' \
  http://localhost:8000/conversations/{id}/text-message
```
