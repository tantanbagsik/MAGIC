from gtts import gTTS
import os
import uuid
from config import config

class VoiceProcessor:
    def __init__(self):
        self.model = None
    
    def transcribe(self, audio_path: str) -> str:
        return "[Voice transcription - Install faster-whisper to enable]"
    
    def text_to_speech(self, text: str, filename: str = None) -> str:
        if filename is None:
            filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join(config.AUDIO_DIR, filename)
        tts = gTTS(text=text, lang="en", slow=False)
        tts.save(filepath)
        return filepath
    
    def save_audio(self, audio_data: bytes, filename: str = None) -> str:
        if filename is None:
            filename = f"{uuid.uuid4()}.webm"
        filepath = os.path.join(config.AUDIO_DIR, filename)
        with open(filepath, "wb") as f:
            f.write(audio_data)
        return filepath

voice_processor = VoiceProcessor()
