import uuid
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Body, Request
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from voice_processor import voice_processor
from llm_service import llm_service
from cache import cache
from config import config

app_state = {"db": None}

async def get_db():
    return app_state["db"]

@asynccontextmanager
async def lifespan(app: FastAPI):
    from database import init_db
    app_state["db"] = await init_db()
    print("Database initialized")
    yield
    await app_state["db"].disconnect()
    print("Database disconnected")

app = FastAPI(title="Voice AI Customer Support", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    cached_status = cache.get("app_status")
    if cached_status:
        return cached_status
    
    status = {"message": "Voice AI Customer Support API", "status": "running", "redis": "connected"}
    cache.set("app_status", status, ttl=60)
    return status

@app.get("/health")
async def health_check():
    ollama_status = llm_service.check_connection()
    redis_status = cache.ping()
    
    health_data = {
        "ollama": "connected" if ollama_status else "disconnected",
        "redis": "connected" if redis_status else "disconnected",
        "model": config.OLLAMA_MODEL
    }
    
    cache.set("health_check", health_data, ttl=30)
    return health_data

@app.post("/conversations")
async def create_conversation(customer_id: Optional[str] = None):
    db = await get_db()
    conversation_id = str(uuid.uuid4())
    conversation = {
        "conversation_id": conversation_id,
        "customer_id": customer_id,
        "status": "active",
        "messages": [],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    }
    await db.get_collection("conversations").insert_one(conversation)
    cache.set(f"conversation:{conversation_id}", conversation, ttl=3600)
    return {"conversation_id": conversation_id}

@app.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    db = await get_db()
    cached = cache.get(f"conversation:{conversation_id}")
    if cached:
        return cached
    
    conversation = await db.get_collection("conversations").find_one({"conversation_id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    cache.set(f"conversation:{conversation_id}", conversation, ttl=1800)
    return conversation

@app.post("/conversations/{conversation_id}/voice-message")
async def process_voice_message(conversation_id: str, audio: UploadFile = File(...)):
    db = await get_db()
    conversation = await db.get_collection("conversations").find_one({"conversation_id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    audio_path = await audio.read()
    audio_filename = f"{uuid.uuid4()}.webm"
    saved_path = voice_processor.save_audio(audio_path, audio_filename)
    
    user_message = voice_processor.transcribe(saved_path)
    
    conversation_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in conversation.get("messages", [])
    ]
    
    ai_response = llm_service.chat(user_message, conversation_history)
    
    now = datetime.utcnow().isoformat()
    
    await db.get_collection("conversations").update_one(
        {"conversation_id": conversation_id},
        {
            "$push": {
                "messages": {
                    "role": "user",
                    "content": user_message,
                    "audio_path": saved_path,
                    "created_at": now
                }
            },
            "$set": {"updated_at": now}
        }
    )
    
    await db.get_collection("conversations").update_one(
        {"conversation_id": conversation_id},
        {
            "$push": {
                "messages": {
                    "role": "assistant",
                    "content": ai_response,
                    "created_at": now
                }
            }
        }
    )
    
    cache.delete(f"conversation:{conversation_id}")
    
    audio_response_path = voice_processor.text_to_speech(ai_response)
    
    cache.set(f"audio:{conversation_id}:{uuid.uuid4()}", {"response": ai_response, "path": audio_response_path}, ttl=300)
    
    return {
        "user_message": user_message,
        "ai_response": ai_response,
        "audio_response": audio_response_path
    }

@app.get("/conversations/{conversation_id}/audio/{filename}")
async def get_audio_response(filename: str):
    filepath = f"{config.AUDIO_DIR}/{filename}"
    return FileResponse(filepath, media_type="audio/mpeg")

@app.post("/conversations/{conversation_id}/text-message")
async def process_text_message(conversation_id: str, request: dict = Body(...)):
    db = await get_db()
    message = request.get("message", "")
    conversation = await db.get_collection("conversations").find_one({"conversation_id": conversation_id})
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    conversation_history = [
        {"role": msg["role"], "content": msg["content"]}
        for msg in conversation.get("messages", [])
    ]
    
    ai_response = llm_service.chat(message, conversation_history)
    
    now = datetime.utcnow().isoformat()
    
    await db.get_collection("conversations").update_one(
        {"conversation_id": conversation_id},
        {
            "$push": {
                "messages": {
                    "role": "user",
                    "content": message,
                    "created_at": now
                }
            },
            "$set": {"updated_at": now}
        }
    )
    
    await db.get_collection("conversations").update_one(
        {"conversation_id": conversation_id},
        {
            "$push": {
                "messages": {
                    "role": "assistant",
                    "content": ai_response,
                    "created_at": now
                }
            }
        }
    )
    
    cache.delete(f"conversation:{conversation_id}")
    
    cache.set(f"response:{conversation_id}:{uuid.uuid4()}", {"user": message, "ai": ai_response}, ttl=300)
    
    return {
        "user_message": message,
        "ai_response": ai_response
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
