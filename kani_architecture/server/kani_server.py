import os
import uuid
import logging
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import torch

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("KaniTTS_Server")

# Конфигурация
AUDIO_DIR = "audio_output"
MODEL_NAME = "nineninesix/kani-tts-450m-0.1-pt"
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# Создаем папку если нет
os.makedirs(AUDIO_DIR, exist_ok=True)

app = FastAPI(title="KaniTTS API Server")

# Глобальная переменная для модели
model = None

class TTSRequest(BaseModel):
    text: str

@app.on_event("startup")
async def load_model():
    """Загрузка модели при старте сервера"""
    global model
    try:
        logger.info(f"⏳ Loading KaniTTS model ({MODEL_NAME}) on {DEVICE}...")
        from kani_tts import KaniTTS
        model = KaniTTS.from_pretrained(MODEL_NAME, device=DEVICE)
        logger.info("✅ Model loaded successfully!")
    except Exception as e:
        logger.critical(f"❌ Failed to load model: {e}")
        # Не падаем, чтобы сервер работал и отдавал 500 ошибку, если что

@app.post("/tts")
async def generate_speech(request: TTSRequest):
    """
    Генерация речи.
    Принимает JSON: {"text": "Привет"}
    Возвращает JSON: {"file": "uuid.wav", "url": "/audio/uuid.wav"}
    """
    if not model:
        raise HTTPException(status_code=503, detail="TTS Model is not loaded")
    
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Empty text")

    try:
        # Генерируем уникальное имя
        filename = f"{uuid.uuid4().hex}.wav"
        file_path = os.path.join(AUDIO_DIR, filename)

        logger.info(f"🗣️ Generating: '{request.text[:30]}...' -> {filename}")

        # Генерация (синхронный вызов, блокирует event loop ненадолго)
        # Для high-load лучше выносить в threadpool, но для одного клиента ок.
        audio = model.generate(request.text)
        model.save_audio(audio, file_path)
        
        return {
            "status": "success",
            "file": filename,
            "url": f"/audio/{filename}"
        }

    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Раздача статики (чтобы скачивать файлы)
app.mount("/audio", StaticFiles(directory=AUDIO_DIR), name="audio")

if __name__ == "__main__":
    logger.info("🚀 Starting TTS Server on port 8000...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
