import logging
import os
import torch
import numpy as np
import soundfile as sf
import io
import edge_tts

logger = logging.getLogger(__name__)

class TTSBrain:
    _kani_model = None
    _use_kani = False

    @classmethod
    def init_kani(cls, model_repo="nineninesix/kani-tts-450m-0.1-pt"):
        """Попытка загрузить Kani TTS"""
        try:
            from transformers import AutoModel
            # Это псевдокод инициализации, так как API Kani может отличаться.
            # Используем спецификацию пользователя:
            # model = KaniTTS.from_pretrained(...)
            
            # Пробуем импорт
            try:
                from kani_tts import KaniTTS
                logger.info(f"⏳ Loading KaniTTS ({model_repo})...")
                cls._kani_model = KaniTTS.from_pretrained(model_repo)
                
                if torch.cuda.is_available():
                    cls._kani_model.to("cuda")
                    
                cls._use_kani = True
                logger.info("✅ KaniTTS Loaded successfully!")
            except ImportError:
                logger.warning("⚠️ kani_tts library not found. Using EdgeTTS fallback.")
                
        except Exception as e:
            logger.error(f"❌ Failed to load KaniTTS: {e}. Fallback to EdgeTTS.")
            cls._use_kani = False

    @classmethod
    async def speak(cls, text: str) -> bytes:
        """
        Главный метод синтеза. Возвращает bytes (audio/wav или audio/mp3).
        """
        # 1. Поробуем Kani
        if cls._use_kani and cls._kani_model:
            try:
                # audio is usually numpy array or tensor
                audio = cls._kani_model.generate(text)
                
                # Convert to bytes
                # Kani save_audio writes to file, let's try to write to buffer if supported
                # Or just write temp file
                
                # Предполагаем, что audio - это Tensor или Numpy
                if hasattr(audio, "cpu"):
                    audio = audio.cpu().numpy()
                
                # Используем SoundFile для записи в буфер
                buffer = io.BytesIO()
                sf.write(buffer, audio, 22050, format='WAV')
                return buffer.getvalue()
                
            except Exception as e:
                logger.error(f"KaniTTS Generation Error: {e}")
                # Fallback to EdgeTTS
        
        # 2. Fallback: EdgeTTS (Cloud, High Quality, Free)
        try:
            logger.info("Speech generation via EdgeTTS...")
            communicate = edge_tts.Communicate(text, "ru-RU-SvetlanaNeural")
            audio_data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_data += chunk["data"]
            return audio_data
        except Exception as e:
            logger.error(f"EdgeTTS Error: {e}")
            return None
