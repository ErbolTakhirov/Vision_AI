import sys

print("⏳ Проверка импорта KaniTTS...")

try:
    from kani_tts import KaniTTS
    print("✅ УСПЕХ! KaniTTS успешно импортирован.")
    print("Можно использовать локальный режим (Plan A).")
except ImportError as e:
    print(f"❌ Ошибка импорта (ImportError): {e}")
    print("Скорее всего, не хватает какой-то DLL или подмодуля NeMo.")
except Exception as e:
    print(f"❌ Общая ошибка: {e}")

print("\nПроверка завершена.")
