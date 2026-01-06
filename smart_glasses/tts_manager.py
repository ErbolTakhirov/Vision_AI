import os
import time
import logging
import threading
import pygame
import soundfile as sf
import numpy as np

# Настройка логирования
logger = logging.getLogger(__name__)

class KaniTTSManager:
    def __init__(self, model_name="nineninesix/kani-tts-450m-0.1-pt", device=None):
        self.model = None
        self.model_name = model_name
        
        # Определяем устройство (CUDA > CPU)
        if device:
            self.device = device
        else:
            import torch
            self.device = "cuda" if torch.cuda.is_available() else "cpu"
        
        logger.info(f"🔊 Инициализация KaniTTS на {self.device}...")
        
        try:
            # Пытаемся импортировать KaniTTS
            try:
                from kani_tts import KaniTTS
                self.model = KaniTTS.from_pretrained(self.model_name)
                # Если у модели есть метод .to(), переносим на девайс
                if hasattr(self.model, "to"):
                    self.model.to(self.device)
                logger.info("✅ KaniTTS успешно загружен!")
            except ImportError:
                logger.error("❌ Библиотека kani_tts не найдена. Убедитесь, что она установлена.")
                logger.warning("⚠️ Используется MOCK режим (генерация тишины) для отладки.")
                self.model = None
                
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки модели: {e}")
            self.model = None

        # Инициализация микшера для воспроизведения
        try:
            pygame.mixer.init()
        except Exception as e:
            logger.error(f"Audio init error: {e}")

    def generate_and_play(self, text, output_file="output.wav"):
        """
        Генерирует аудио и сразу запускает воспроизведение (неблокирующее).
        """
        if not text:
            return

        logger.info(f"🗣 Генерация речи: '{text}'")
        start_time = time.time()

        try:
            if self.model:
                # Генерация аудио (согласно вашему API)
                audio = self.model.generate(text)
                
                # Сохранение
                self.model.save_audio(audio, output_file)
            else:
                # Mock генерация для тестов без модели
                logger.warning("[MOCK] Генерирую заглушку...")
                self._generate_mock_audio(output_file)

            gen_time = time.time() - start_time
            logger.info(f"⚡ TTS занял {gen_time:.2f} сек.")

            # Воспроизведение
            self._play_file(output_file)

        except Exception as e:
            logger.error(f"Ошибка TTS: {e}")

    def _play_file(self, file_path):
        """Проигрывает файл через Pygame без блокировки основного потока"""
        try:
            if pygame.mixer.music.get_busy():
                pygame.mixer.music.stop()
            
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
        except Exception as e:
            logger.error(f"Ошибка воспроизведения: {e}")

    def _generate_mock_audio(self, filename):
        """Создает пустой WAV файл для тестов"""
        samplerate = 22050
        data = np.zeros(samplerate) # 1 секунда тишины
        sf.write(filename, data, samplerate)

    def is_busy(self):
        return pygame.mixer.music.get_busy()

    def stop(self):
        pygame.mixer.music.stop()
