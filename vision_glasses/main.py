import logging
import time
import sys
import os

# Добавляем текущую директорию в путь, чтобы импорты работали
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from core.user_memory import UserMemory
from core.context_manager import ContextManager
from core.user_state import UserState
from core.dialog_manager import DialogManager
from core.tts_manager import TTSManager

# Настройка логера
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger("Main")

def main():
    logger.info("=== 👓 Vision AI Glasses MVP (CAG Architecture) ===")
    
    # 1. Init Layers
    memory = UserMemory(Config.USER_PROFILE_PATH)
    ctx_mgr = ContextManager()
    state = UserState()
    tts = TTSManager(Config.TTS_MODEL_REPO, Config.DEVICE)
    dialog = DialogManager(memory, state)
    
    logger.info("Система готова. 'q' для выхода.")
    
    # Main Loop
    while True:
        try:
            # A. Emulate Sensor Inputs (В реальности тут цикл камеры и микрофона)
            # Для теста вводим текст с клавиатуры
            user_input = input("\n👤 Вы (текст): ").strip()
            if user_input.lower() in ['q', 'exit']:
                break
            
            # B. Update Context
            # Эмулируем, что камера видит "ноутбук" и "кофе"
            ctx_mgr.update_vision(["ноутбук", "чашка кофе"])
            ctx_mgr.update_speech(user_input)
            
            context_data = ctx_mgr.build_context_dict()
            
            # C. Generate Affective Response
            response = dialog.generate_response(context_data)
            
            # D. Output
            print(f"🤖 Vision AI: {response}")
            tts.speak(response)
            
        except KeyboardInterrupt:
            print("\nВыход...")
            break
        except Exception as e:
            logger.error(f"Critical Loop Error: {e}")

if __name__ == "__main__":
    main()
