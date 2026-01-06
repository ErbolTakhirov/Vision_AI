import os

class Config:
    # === Main Settings ===
    LANGUAGE = "ru"  # ru / en / ky
    DEVICE = "cuda" if os.environ.get("CUDA_VISIBLE_DEVICES") else "cpu"
    
    # === Paths ===
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    USER_PROFILE_PATH = os.path.join(BASE_DIR, "data", "user_profile.json")
    
    # === TTS Settings ===
    TTS_MODEL_REPO = "nineninesix/kani-tts-450m-0.1-pt"
    TTS_SPEED = 1.0
    
    # === Parameters ===
    # Сколько последних взаимодействий хранить в памяти для промпта
    MEMORY_WINDOW_SIZE = 5
    
    # Пороги уверенности
    CONFIDENCE_THRESHOLD = 0.5
    
    # === Debug ===
    DEBUG_MODE = True
