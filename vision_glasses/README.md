# Vision AI Glasses (CAG Architecture)

Модуль "умных очков" с Context-Affect-Guidance архитектурой и Kani TTS.

## Структура
* `core/` - Основная логика (Memory, State, Dialog)
* `data/` - Файл профиля пользователя
* `main.py` - Запуск

## Установка
1. Создайте окружение (если нет):
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
3. Установите Kani TTS (если не в pip):
   ```bash
   pip install git+https://github.com/nineninesix/kani-tts.git
   ```

## Запуск
```bash
python main.py
```
Вводите текст в консоль для диалога.
Система будет имитировать, что видит "ноутбук" и "кофе" (см. `main.py` для изменения).
