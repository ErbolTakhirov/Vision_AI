import os
import requests
import logging
import time

try:
    import pygame
except ImportError:
    pygame = None

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("TTSClient")

class KaniTTSClient:
    def __init__(self, server_url="http://127.0.0.1:8000", output_dir="temp"):
        """
        :param server_url: URL сервера без слэша в конце (напр http://localhost:8000)
        :param output_dir: Папка для сохранения скачанных wav
        """
        self.base_url = server_url
        self.output_dir = output_dir
        
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Init player
        if pygame:
            try:
                pygame.mixer.init()
            except Exception as e:
                logger.error(f"Pygame mixer init failed: {e}")

    def tts_to_file(self, text: str) -> str:
        """
        Отправляет запрос на сервер, скачивает файл и возвращает путь.
        """
        try:
            logger.info(f"🌐 Sending request: '{text[:20]}...'")
            response = requests.post(f"{self.base_url}/tts", json={"text": text}, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"Server error {response.status_code}: {response.text}")
                return None
                
            data = response.json()
            file_url_path = data.get("url") # /audio/xyz.wav
            
            if not file_url_path:
                logger.error("No URL in response")
                return None
                
            # Скачиваем файл
            # Формируем полный URL: http://localhost:8000/audio/xyz.wav
            download_url = f"{self.base_url}{file_url_path}"
            
            local_filename = os.path.join(self.output_dir, f"tts_{int(time.time())}.wav")
            
            with requests.get(download_url, stream=True) as r:
                r.raise_for_status()
                with open(local_filename, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192): 
                        f.write(chunk)
                        
            logger.info(f"💾 Saved to: {local_filename}")
            return local_filename

        except requests.exceptions.ConnectionError:
            logger.critical("❌ Could not connect to TTS Server. Is it running?")
            return None
        except Exception as e:
            logger.error(f"Client error: {e}")
            return None

    def speak(self, text: str):
        """Скачивает и сразу проигрывает"""
        file_path = self.tts_to_file(text)
        if file_path and pygame:
            self._play_audio(file_path)
            
    def _play_audio(self, path):
        try:
            pygame.mixer.music.load(path)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                time.sleep(0.1)
        except Exception as e:
            logger.error(f"Playback error: {e}")
