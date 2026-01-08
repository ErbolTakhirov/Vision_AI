import os
import uuid
import logging
import torch
import numpy as np
from typing import Optional, Union

# Импортируем конфиг из текущей папки
try:
    from config import TTSConfig
except ImportError:
    # Fallback если запускаем не из корня
    from .config import TTSConfig

# Настройка логгера
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TTSManager")

class TTSManager:
    """
    Менеджер для работы с KaniTTS.
    Обеспечивает загрузку модели, генерацию речи и сохранение в файл.
    """
    
    def __init__(self, model_name: str = TTSConfig.MODEL_NAME, device: Optional[str] = None):
        self.model_name = model_name
        self.device = device if device else TTSConfig.DEVICE
        self.model = None
        
        self._load_model()

    def _load_model(self):
        """Загружает модель KaniTTS в память."""
        try:
            logger.info(f"⏳ Loading KaniTTS model: {self.model_name} on {self.device}...")
            
            from kani_tts import KaniTTS
            
            self.model = KaniTTS.from_pretrained(
                self.model_name, 
                device=self.device
            )
            logger.info("✅ KaniTTS model loaded successfully.")
            
        except ImportError:
            logger.critical("❌ Library 'kani-tts' not found. Please install it: pip install kani-tts")
            raise
        except Exception as e:
            logger.critical(f"❌ Failed to load KaniTTS model: {e}")
            raise

    def tts_to_file(self, text: str, filename: Optional[str] = None) -> Optional[str]:
        """
        Генерирует речь из текста и сохраняет в файл.
        
        :param text: Текст для озвучки
        :param filename: Имя файла (опционально). Если нет - генерируется UUID.
        :return: Абсолютный путь к сохраненному файлу или None при ошибке.
        """
        if not text or not text.strip():
            logger.warning("TTS recieved empty text. Skipping.")
            return None
            
        if self.model is None:
            logger.error("TTS Model is not loaded.")
            return None

        try:
            # Генерация уникального имени если не задано
            if not filename:
                filename = f"tts_{uuid.uuid4().hex[:8]}.wav"
            
            # Убедимся, что путь полный
            full_path = os.path.join(TTSConfig.OUTPUT_PATH, filename)
            
            # 1. Генерация аудио (возвращает Tensor или Array)
            # KaniTTS API: audio = model.generate(text)
            logger.info(f"🗣️ Generating speech for: '{text[:20]}...'")
            audio = self.model.generate(text)
            
            # 2. Сохранение
            # KaniTTS API: model.save_audio(audio, path)
            self.model.save_audio(audio, full_path)
            
            logger.info(f"💾 Audio saved to: {full_path}")
            return full_path

        except Exception as e:
            logger.error(f"❌ Error during TTS generation: {e}")
            return None

    def tts_to_buffer(self, text: str):
        """
        Возвращает raw audio data (опционально, если нужно для stream play).
        Пока не реализовано, т.к. KaniTTS сохраняет в файл лучше.
        """
        pass
