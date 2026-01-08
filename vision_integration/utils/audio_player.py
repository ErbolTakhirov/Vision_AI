import os
import time
import logging

try:
    import pygame
except ImportError:
    pygame = None

logger = logging.getLogger(__name__)

class AudioPlayer:
    """
    Класс для воспроизведения аудиофайлов через pygame.mixer.
    Обеспечивает неблокирующее воспроизведение.
    """
    def __init__(self):
        if pygame:
            try:
                pygame.mixer.init()
                logger.info("✅ AudioPlayer initialized (pygame)")
            except Exception as e:
                logger.error(f"❌ Failed to init pygame mixer: {e}")
                self.disabled = True
        else:
            logger.warning("⚠️ Pygame not found. Audio playback disabled.")
            self.disabled = True
            
    def play(self, file_path: str, block: bool = False):
        """
        Воспроизводит аудиофайл.
        :param file_path: Путь к файлу (.wav, .mp3)
        :param block: Если True, ждет окончания воспроизведения
        """
        if getattr(self, 'disabled', False) or not pygame:
            logger.warning(f"Audio playback skipped for: {file_path}")
            return

        if not os.path.exists(file_path):
            logger.error(f"Audio file not found: {file_path}")
            return

        try:
            # Загружаем и играем
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            
            logger.info(f"▶️ Playing: {os.path.basename(file_path)}")
            
            if block:
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(10)
                    
        except Exception as e:
            logger.error(f"Error playing audio: {e}")

    def stop(self):
        """Останавливает воспроизведение"""
        if not getattr(self, 'disabled', False) and pygame:
            pygame.mixer.music.stop()

    def is_playing(self):
        if not getattr(self, 'disabled', False) and pygame:
            return pygame.mixer.music.get_busy()
        return False
