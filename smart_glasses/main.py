import cv2
import time
import logging
import colorama
from colorama import Fore, Style

from tts_manager import KaniTTSManager
from vision_service import VisionSystem

# Инициализация цвета
colorama.init(autoreset=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("SmartGlasses")

def mock_llm_response(detected_objects):
    """
    Эмуляция LLM. В реальности здесь будет вызов OpenAI/DeepSeek/LlamaCpp.
    """
    if not detected_objects:
        return None
        
    obj_str = ", ".join(detected_objects)
    
    # KaniTTS поддерживает русский и кыргызский
    # Для теста будем чередовать или использовать русский
    
    responses = [
        f"Я вижу {obj_str}.",
        f"Перед вами {obj_str}.",
        f"Осторожно, впереди {obj_str}."
    ]
    return responses[0]

def main():
    logger.info(Fore.CYAN + "=== 🕶️ Smart Glasses OS v1.0 (KaniTTS Edition) ===")
    
    # 1. Init Modules
    tts = KaniTTSManager()
    vision = VisionSystem()
    cap = cv2.VideoCapture(0) # 0 - Default Camera

    if not cap.isOpened():
        logger.error("Не удалось открыть камеру!")
        return

    logger.info("Нажмите 'q' для выхода, 's' для принудительного сканирования.")

    last_scan_time = 0
    SCAN_INTERVAL = 5.0 # Сканируем каждые 5 сек чтобы не болтать без умолку

    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            current_time = time.time()
            
            # Отображаем камеру (для дебага на мониторе)
            cv2.imshow('Smart Glasses Debug', frame)

            # Key controls
            key = cv2.waitKey(1) & 0xFF
            if key == ord('q'):
                break
            
            # Автоматическое сканирование или по кнопке
            manual_trigger = (key == ord('s'))
            
            if manual_trigger or (current_time - last_scan_time > SCAN_INTERVAL):
                # Не прерываем, если TTS еще говорит (чтобы не было каши)
                if tts.is_busy() and not manual_trigger:
                    continue

                logger.info(Fore.YELLOW + "🔍 Сканирование...")
                last_scan_time = current_time
                
                # 1. Vision
                objects = vision.detect(frame)
                
                if objects:
                    logger.info(f"Объекты: {objects}")
                    
                    # 2. LLM (Thought)
                    response_text = mock_llm_response(objects)
                    
                    # 3. TTS (Voice)
                    if response_text:
                        print(f"{Fore.GREEN}🤖 AI: {response_text}")
                        # Генерируем и говорим
                        tts.generate_and_play(response_text)
                else:
                    logger.info("Ничего интересного.")

    except KeyboardInterrupt:
        logger.info("Остановка...")
    finally:
        cap.release()
        cv2.destroyAllWindows()
        tts.stop()
        logger.info("Система выключена.")

if __name__ == "__main__":
    main()
