# Audio Settings
SAMPLE_RATE = 16000
CHUNK_SIZE = 1024
PAUSE_THRESHOLD = 0.8  # Seconds of silence to consider the phrase complete

# Dialogue Settings
WAKE_WORDS = [
    "a vision", "hey vision", "a-vision", "avision", "avis", 
    "эй вижн", "вижн", "эй вижу", "вижу", "эй вижен", "вижен",
    "эй биржан", "биржан", "эй вежн", "вежн", "a vision"
]
ACTIVE_MODE_TIMEOUT = 10  # Seconds to wait for follow-up before going IDLE

# TTS Settings
TTS_RATE = 175
TTS_VOLUME = 1.0

import os
from dotenv import load_dotenv

load_dotenv()

# API Keys (Load from env in production)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY") 
