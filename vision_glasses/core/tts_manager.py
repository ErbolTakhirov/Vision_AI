import logging
import pygame
import os
import time

# Попытка импорта, чтобы не падать при отсутствии пакета
try:
    from kani_tts import KaniTTS
    KANI_AVAILABLE = True
except ImportError:
    KANI_AVAILABLE = False

logger = logging.getLogger(__name__)

class TTSManager:
    """
    Управляет синтезом речи через Kani TTS.
    """
    def __init__(self, model_repo, device="cpu"):
        self.device = device
        self.model = None
        
        # Init Audio
        try:
            pygame.mixer.init()
        except Exception:
            pass

        if KANI_AVAILABLE:
            logger.info("⏳ Загрузка Kani TTS модели...")
            try:
                self.model = KaniTTS.from_pretrained(model_repo)
                if hasattr(self.model, "to"):
                    self.model.to(self.device)
                logger.info("✅ Kani TTS готова.")
            except Exception as e:
                logger.error(f"TTS Load Error: {e}")
        else:
            logger.warning("⚠️ KaniTTS библиотека не найдена. Режим заглушки.")

    def speak(self, text: str, output_file="output.wav"):
        if not text:
            return

        logger.info(f"🔊 Speak: {text}")
        
        if self.model:
            try:
                audio = self.model.generate(text)
                self.model.save_audio(audio, output_file)
                self._play_audio(output_file)
            except Exception as e:
                logger.error(f"TTS Gen Error: {e}")
        else:
            # Mock play
            logger.info("(Mock Audio Playing...)")
            time.sleep(1) 

    def _play_audio(self, file_path):
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            # Ждем пока договорит (блокирующий режим для диалога)
            # В реальных очках лучше сделать очередь
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
        except Exception as e:
            logger.error(f"Playback Error: {e}")
