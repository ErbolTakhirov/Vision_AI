import sys
import time
import logging
from pathlib import Path

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("Main")

# Импорты модулей
try:
    from tts_manager import TTSManager
    from utils.audio_player import AudioPlayer
    import config
except ImportError as e:
    logger.error(f"Failed to import modules: {e}")
    sys.exit(1)

def mock_ai_response(user_input: str) -> str:
    """
    Эмуляция ответа ИИ. В реальном проекте тут будет вызов LLM (DeepSeek/GPT).
    """
    responses = {
        "привет": "Привет! Я готов к работе. Чем могу помочь?",
        "кто ты": "Я голосовой ассистент с передовой системой синтеза речи KaniTTS.",
        "пока": "До свидания! Обращайтесь, если я понадоблюсь.",
    }
    return responses.get(user_input.lower(), f"Я услышал: {user_input}. Повторите, пожалуйста, или спросите что-то еще.")

def main():
    print("="*50)
    print("🤖 VISION AI: TTS Demo (KaniTTS Integration)")
    print("="*50)
    
    # 1. Инициализация Audio Player
    player = AudioPlayer()
    
    # 2. Инициализация TTS (Это может занять время на загрузку модели)
    try:
        print("⏳ Initializing TTS Engine (this may take a few seconds)...")
        tts = TTSManager()
        print("✅ TTS Engine Ready!")
    except Exception as e:
        logger.critical(f"Critical error initializing TTS: {e}")
        print("\n❌ Ошибка запуска. Проверьте requirements.txt и установку kani-tts.")
        return

    print("\n💬 Введите текст для озвучивания (или 'exit' для выхода):")
    
    # 3. Основной цикл
    while True:
        try:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'выход']:
                print("👋 Exiting...")
                break
                
            # Получаем ответ от "ИИ"
            ai_text = mock_ai_response(user_input)
            print(f"🤖 AI: {ai_text}")
            
            # Генерируем речь
            start_time = time.time()
            audio_path = tts.tts_to_file(ai_text)
            generation_time = time.time() - start_time
            
            if audio_path:
                print(f"⚡ Generated in {generation_time:.2f}s")
                
                # Воспроизводим
                if player:
                    player.play(audio_path, block=True) # Блокируем, чтобы не прерывать ввод
                else:
                    print(f"🔊 [Audio generated at: {audio_path}]")
            else:
                print("❌ Failed to generate audio.")
                
        except KeyboardInterrupt:
            print("\n👋 Interrupted.")
            break
        except Exception as e:
            logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()
