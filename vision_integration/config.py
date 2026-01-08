import os
import torch
from pathlib import Path

# Базовая директория модуля
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output_audio"

# Автоматически создаем папку для вывода, если её нет
os.makedirs(OUTPUT_DIR, exist_ok=True)

class TTSConfig:
    """
    Конфигурация для модуля синтеза речи (KaniTTS).
    """
    
    # Имя модели в HuggingFace Hub
    # nineninesix/kani-tts-450m-0.1-pt - стандартная PyTorch версия
    MODEL_NAME = "nineninesix/kani-tts-450m-0.1-pt"
    
    # Определение устройства (GPU/CPU)
    # Если доступна CUDA, используем её. Иначе CPU.
    # Можно принудительно задать "cpu" или "cuda:0"
    DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
    
    # Директория для сохранения .wav файлов
    OUTPUT_PATH = OUTPUT_DIR
    
    # Частота дискретизации (обычно определяется моделью, но можно использовать для плеера)
    SAMPLE_RATE = 24000
