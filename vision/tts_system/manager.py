import os
import uuid
import logging
from django.conf import settings
from .config import TTSConfig

logger = logging.getLogger(__name__)

class TTSManager:
    _instance = None
    _model = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TTSManager, cls).__new__(cls)
            cls._instance._load_model()
        return cls._instance

    def _load_model(self):
        """Ленивая загрузка модели (Singleton)"""
        if self._model:
            return

        # Temporarily disabled KaniTTS as per request
        logger.info(f"Skipping KaniTTS loader. Using EdgeTTS fallback.")
        self._model = None
        # try:
        #     logger.info(f"⏳ Loading KaniTTS model: {TTSConfig.MODEL_NAME}...")
        #     from kani_tts import KaniTTS
        #     self._model = KaniTTS.from_pretrained(TTSConfig.MODEL_NAME, device=TTSConfig.DEVICE)
        #     logger.info("✅ KaniTTS model loaded successfully.")
        # except ImportError:
        #     logger.warning("⚠️ kani-tts library not found. Using EdgeTTS fallback.")
        #     self._model = None
        # except Exception as e:
        #     logger.error(f"❌ Failed to load KaniTTS: {e}")
        #     self._model = None

    async def generate_speech(self, text: str) -> str:
        """
        Генерирует речь и возвращает RELATIVE URL к файлу (например, /media/tts/xyz.wav).
        Асинхронный метод для Django views.
        """
        filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
        full_path = os.path.join(TTSConfig.OUTPUT_PATH, filename)
        
        # 1. Попытка использовать KaniTTS
        if self._model:
            try:
                # KaniTTS sync generation (нужно запускать в threadpool, если блокирует)
                # Но пока сделаем синхронно, т.к. generate достаточно быстр на GPU
                audio = self._model.generate(text)
                self._model.save_audio(audio, full_path)
                
                # Возвращаем URL
                return f"{TTSConfig.MEDIA_URL}{filename}"
            except Exception as e:
                logger.error(f"KaniTTS generation failed: {e}. Falling back to EdgeTTS.")

        # 2. Fallback на EdgeTTS (если Kani нет или ошибка)
        try:
            import edge_tts
            communicate = edge_tts.Communicate(text, "ru-RU-DmitryNeural") # Default to Russian
            await communicate.save(full_path)
            return f"{TTSConfig.MEDIA_URL}{filename}"
        except Exception as e:
            logger.error(f"EdgeTTS failed: {e}")
            return None
