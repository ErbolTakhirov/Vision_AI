import time
from tts_client import KaniTTSClient

def main():
    print("="*50)
    print("🎓 Vision AI: Remote TTS Client")
    print("="*50)
    
    # 1. Настройка URL сервера
    # Если сервер запущен в WSL на этой же машине -> http://localhost:8000
    # Если на другой машине -> http://192.168.x.x:8000
    SERVER_URL = "http://127.0.0.1:8000" 
    
    client = KaniTTSClient(server_url=SERVER_URL)
    
    print(f"📡 Connecting to server at: {SERVER_URL}")
    print("Type text to speak (or 'q' to quit)")
    
    while True:
        text = input("\ntext > ").strip()
        if text.lower() in ['q', 'exit']:
            break
            
        if not text:
            continue
            
        print("⏳ Processing...")
        start = time.time()
        client.speak(text)
        print(f"✅ Done in {time.time() - start:.2f}s")

if __name__ == "__main__":
    main()
