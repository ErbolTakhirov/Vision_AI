# Интеграция KaniTTS в Vision AI

Этот модуль обеспечивает синтез речи с использованием модели KaniTTS.

## ⚠️ Важно: Установка PyTorch

По умолчанию `pip install torch` может установить версию без поддержки GPU. 
Для максимальной производительности установите PyTorch вручную перед остальными пакетами.

### Если у вас есть NVIDIA GPU (рекомендуется):
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
```
*(Замените `cu118` на `cu121` если у вас свежие драйвера CUDA 12.x)*

### Если у вас только CPU:
```bash
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
```

## Установка зависимостей

После установки PyTorch выполните:
```bash
pip install -r requirements.txt
```

## Запуск демо

```bash
python main.py
```
Это запустит консольный чат, где любой ваш ввод будет озвучен нейросетью.

## Использование в коде

```python
from tts_manager import TTSManager

tts = TTSManager()
filepath = tts.tts_to_file("Привет, я твой ИИ помощник.")

# Воспроизведение (нужен модуль audio_player или свой плеер)
from utils.audio_player import AudioPlayer
player = AudioPlayer()
player.play(filepath)
```
