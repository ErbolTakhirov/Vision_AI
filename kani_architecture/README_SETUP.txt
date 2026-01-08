# Инструкция по запуску KaniTTS (Клиент-Сервер)

## 1. СЕРВЕР (WSL2 / Linux)
Этот код нужно запускать там, где работает NVIDIA-драйвер и Linux (например, Ubuntu в WSL).

1. Перейдите в папку server:
   cd kani_architecture/server

2. Создайте venv:
   python3 -m venv venv
   source venv/bin/activate

3. Установите библиотеки:
   pip install -r requirements_server.txt

4. Запустите сервер:
   python3 kani_server.py

Сервер запустится на порту 8000. Проверьте: http://localhost:8000/docs

---

## 2. КЛИЕНТ (Windows)
Этот код запускается в вашем основном окружении Windows.

1. Перейдите в папку client:
   cd kani_architecture\client

2. Установите библиотеки (можно в ваше основное venv):
   pip install -r requirements_client.txt

3. Запустите клиент:
   python main.py

4. Введите текст, и вы должны услышать голос!

---

## Интеграция в основной проект Vision AI

Просто скопируйте `tts_client.py` в ваш проект и используйте класс `KaniTTSClient` вместо локальных вызовов TTS.
