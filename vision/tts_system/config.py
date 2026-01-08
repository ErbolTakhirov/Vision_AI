import os
from pathlib import Path
from django.conf import settings

# Определяем папку для сохранения аудио внутри MEDIA_ROOT
# Чтобы Flutter мог скачать файл по ссылке http://server/media/tts/file.wav
OUTPUT_DIR = os.path.join(settings.MEDIA_ROOT, 'tts')

# Создаем папку, если нет
os.makedirs(OUTPUT_DIR, exist_ok=True)

class TTSConfig:
    # Имя модели
    MODEL_NAME = "nineninesix/kani-tts-450m-0.1-pt"
    
    # Device (зависит от сервера)
    import torch
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Путь для сохранения
    OUTPUT_PATH = OUTPUT_DIR
    
    # URL префикс (для формирования ссылки)
    MEDIA_URL = settings.MEDIA_URL + 'tts/'
