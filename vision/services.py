import os
import asyncio
import base64
import torch
from faster_whisper import WhisperModel
from transformers import BlipProcessor, BlipForConditionalGeneration
from PIL import Image
from io import BytesIO
from openai import AsyncOpenAI
import edge_tts
import logging
import easyocr
import numpy as np
from ultralytics import YOLO

logger = logging.getLogger(__name__)

class LocalBrain:
    _stt_model = None
    _vision_model = None
    _vision_processor = None
    _ocr_reader = None
    _yolo_model = None
    
    @classmethod
    def get_stt_model(cls):
        if cls._stt_model is None:
            print("⏳ Загрузка модели Whisper (STT)...")
            device = "cuda" if torch.cuda.is_available() else "cpu"
            compute_type = "float16" if device == "cuda" else "int8"
            
            try:
                cls._stt_model = WhisperModel("base", device=device, compute_type=compute_type)
                print(f"✅ Whisper загружен на {device}")
            except Exception as e:
                print(f"❌ Ошибка загрузки Whisper: {e}")
                cls._stt_model = WhisperModel("tiny", device="cpu", compute_type="int8")
        return cls._stt_model

    @classmethod
    def get_vision_model(cls):
        if cls._vision_model is None:
            print("⏳ Загрузка модели Vision (BLIP)...")
            try:
                cls._vision_processor = BlipProcessor.from_pretrained("Salesforce/blip-image-captioning-base")
                cls._vision_model = BlipForConditionalGeneration.from_pretrained("Salesforce/blip-image-captioning-base")
                
                device = "cuda" if torch.cuda.is_available() else "cpu"
                cls._vision_model.to(device)
                print(f"✅ Vision модель загружена на {device}")
            except Exception as e:
                print(f"❌ Ошибка загрузки Vision: {e}")
        return cls._vision_processor, cls._vision_model

    @classmethod
    def get_ocr_reader(cls):
        if cls._ocr_reader is None:
             print("⏳ Загрузка EasyOCR...")
             # Инициализируем только русский и английский
             cls._ocr_reader = easyocr.Reader(['ru', 'en'], gpu=torch.cuda.is_available())
             print("✅ EasyOCR загружен")
        return cls._ocr_reader

    @classmethod
    def get_yolo_model(cls):
        if cls._yolo_model is None:
            print("⏳ Загрузка YOLO...")
            try:
                cls._yolo_model = YOLO("yolov8n.pt") # Nano model for speed
                print("✅ YOLO загружен")
            except Exception as e:
                 print(f"❌ Ошибка загрузки YOLO: {e}")
        return cls._yolo_model

def speech_to_text(audio_file):
    model = LocalBrain.get_stt_model()
    if not model:
        return None
    try:
        segments, info = model.transcribe(audio_file, beam_size=5)
        text = " ".join([segment.text for segment in segments])
        return text.strip()
    except Exception as e:
        logger.error(f"STT Error: {e}")
        return None

def analyze_image_local(image_bytes):
    processor, model = LocalBrain.get_vision_model()
    if not model:
        return "Ошибка загрузки зрения."
    try:
        image = Image.open(BytesIO(image_bytes)).convert('RGB')
        device = "cuda" if torch.cuda.is_available() else "cpu"
        inputs = processor(images=image, return_tensors="pt").to(device)
        out = model.generate(**inputs, max_new_tokens=50)
        description = processor.decode(out[0], skip_special_tokens=True)
        return description
    except Exception as e:
        logger.error(f"Vision Error: {e}")
        return "Не удалось распознать изображение."

def read_text_local(image_bytes):
    reader = LocalBrain.get_ocr_reader()
    try:
        result = reader.readtext(image_bytes, detail=0)
        text = " ".join(result)
        return text if text else None
    except Exception as e:
        logger.error(f"OCR Error: {e}")
        return None

def detect_objects_local(image_bytes):
    model = LocalBrain.get_yolo_model()
    if not model: return []
    try:
        import cv2 # Local import to avoid top-level fail if missing
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if img is None:
            return []
        
        # Preprocessing для улучшения распознавания
        # 1. Resize если изображение слишком большое
        max_dimension = 1280
        h, w = img.shape[:2]
        if max(h, w) > max_dimension:
            scale = max_dimension / max(h, w)
            img = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
        
        # 2. Улучшение контраста (CLAHE)
        lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        img = cv2.cvtColor(cv2.merge([l, a, b]), cv2.COLOR_LAB2BGR)
        
        # Детекция с оптимальными параметрами
        results = model.predict(img, conf=0.3, iou=0.45, verbose=False)
        detected = []
        for r in results:
            for c in r.boxes.cls:
                detected.append(model.names[int(c)])
        return list(set(detected))
    except Exception as e:
        print(f"YOLO Error: {e}")
        return []

async def generate_ai_response_async(user_text, visual_context=None, user_obj=None, ocr_context=None):
    """
    Генерирует ответ используя DeepSeek/OpenRouter API.
    Поддерживает сохранение фактов (Memory).
    """
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "Ошибка: Не найден API ключ (OPENAI_API_KEY)."

    # Определяем endpoint и модель
    base_url = "https://api.deepseek.com"
    model_name = "deepseek-chat"
    if api_key.startswith("sk-or-v1"):
        base_url = "https://openrouter.ai/api/v1"
        model_name = "deepseek/deepseek-chat"

    client = AsyncOpenAI(api_key=api_key, base_url=base_url)

    # Формируем промпт с учетом памяти
    system_prompt = "Ты голосовой помощник для незрячих. Твои ответы должны быть лаконичными, теплыми и полезными. Отвечай на русском языке."
    
    # Добавляем факты из памяти пользователя
    if user_obj and user_obj.facts:
        facts_str = ", ".join([f"{k}: {v}" for k,v in user_obj.facts.items()])
        system_prompt += f"\n\nПамятка (известные факты): {facts_str}"

    prompt = user_text
    
    # Добавляем визуальный контекст
    context_parts = []
    if visual_context:
        context_parts.append(f"Визуально (BLIP): {visual_context}")
    if ocr_context:
        context_parts.append(f"Текст на изображении (OCR): {ocr_context}")
        
    if context_parts:
        prompt = f"Контекст изображения:\n" + "\n".join(context_parts) + f"\n\nВопрос: {user_text}"
    
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt}
    ]
    
    # Проверка на намерение "Запомни" (простая эвристика)
    # Если бот поймет, что нужно запомнить, он сделает это.
    # Но для надежности добавим инструкцию в промпт или обработаем отдельно.
    # Пусть пока просто отвечает, а "запоминание" сделаем через ключевые слова.
    if user_text.lower().startswith("запомни") and user_obj:
        # Пытаемся извлечь факт. Для простоты сохраняем raw текст пока, 
        # или просим модель выделить JSON (сложно для текстового чата).
        # Простой вариант:
        user_obj.facts['last_memory'] = user_text
        # В реальности тут нужен NLP парсер "entity -> description".
        # Пока просто скажем пользователю ок.
        pass

    try:
        response = await client.chat.completions.create(
            model=model_name,
            messages=messages,
            max_tokens=500
        )
        answer = response.choices[0].message.content
        
        # Пост-процессинг для сохранения памяти через спец-теги, если модель умная
        # (Пропустим для MVP)
        
        return answer
    except Exception as e:
        logger.error(f"DeepSeek API Error: {e}")
        return f"Ошибка API ИИ: {e}"


async def text_to_speech_async(text):
    communicate = edge_tts.Communicate(text, "ru-RU-SvetlanaNeural")
    try:
        audio_data = b""
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_data += chunk["data"]
        return audio_data
    except Exception as e:
        logger.error(f"TTS Error: {e}")
        return None

def get_ai_response_sync(text, visual_context=None):
    return asyncio.run(generate_ai_response_async(text, visual_context))

def get_tts_sync(text):
    return asyncio.run(text_to_speech_async(text))
