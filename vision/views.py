from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from .yolo import model
import cv2
import numpy as np
from PIL import Image
import io

# Маппинг классов на русский
CLASS_NAMES_RU = {
    'person': 'человек',
    'bicycle': 'велосипед',
    'car': 'автомобиль',
    'motorcycle': 'мотоцикл',
    'airplane': 'самолет',
    'bus': 'автобус',
    'train': 'поезд',
    'truck': 'грузовик',
    'boat': 'лодка',
    'traffic light': 'светофор',
    'fire hydrant': 'пожарный гидрант',
    'stop sign': 'знак стоп',
    'parking meter': 'парвокочный автомат',
    'bench': 'скамейка',
    'bird': 'птица',
    'cat': 'кошка',
    'dog': 'собака',
    'horse': 'лошадь',
    'sheep': 'овца',
    'cow': 'корова',
    'elephant': 'слон',
    'bear': 'медведь',
    'zebra': 'зебра',
    'giraffe': 'жираф',
    'backpack': 'рюкзак',
    'umbrella': 'зонтик',
    'handbag': 'сумка',
    'tie': 'галстук',
    'suitcase': 'чемодан',
    'frisbee': 'фрисби',
    'skis': 'лыжи',
    'snowboard': 'сноуборд',
    'sports ball': 'мяч',
    'kite': 'воздушный змей',
    'baseball bat': 'бейсбольная бита',
    'baseball glove': 'бейсбольная перчатка',
    'skateboard': 'скейтборд',
    'surfboard': 'серфборд',
    'tennis racket': 'теннисная ракетка',
    'bottle': 'бутылка',
    'wine glass': 'бокал вина',
    'cup': 'чашка',
    'fork': 'вилка',
    'knife': 'нож',
    'spoon': 'ложка',
    'bowl': 'миска',
    'banana': 'банан',
    'apple': 'яблоко',
    'sandwich': 'сэндвич',
    'orange': 'апельсин',
    'broccoli': 'брокколи',
    'carrot': 'морковь',
    'hot dog': 'хот-дог',
    'pizza': 'пицца',
    'donut': 'пончик',
    'cake': 'торт',
    'chair': 'стул',
    'couch': 'диван',
    'potted plant': 'растение в горшке',
    'bed': 'кровать',
    'dining table': 'обеденный стол',
    'toilet': 'туалет',
    'tv': 'телевизор',
    'laptop': 'ноутбук',
    'mouse': 'мышь',
    'remote': 'пульт',
    'keyboard': 'клавиатура',
    'cell phone': 'телефон',
    'microwave': 'микроволновка',
    'oven': 'печь',
    'toaster': 'тостер',
    'sink': 'раковина',
    'refrigerator': 'холодильник',
    'book': 'книга',
    'clock': 'часы',
    'vase': 'ваза',
    'scissors': 'ножницы',
    'teddy bear': 'плюшевый мишка',
    'hair drier': 'фен',
    'toothbrush': 'зубная щетка'
}

@method_decorator(csrf_exempt, name='dispatch')
class DetectAPIView(View):
    def post(self, request, *args, **kwargs):
        if 'image' not in request.FILES:
            return JsonResponse({'message': 'Нет изображения'}, status=400)

        # Читаем изображение
        image_file = request.FILES['image']
        image_bytes = image_file.read()
        
        # Конвертируем в OpenCV формат
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if img is None:
            return JsonResponse({'message': 'Ошибка обработки изображения'}, status=400)

        # Детекция (confidence ~0.4 как в ТЗ)
        results = model.predict(img, conf=0.4)
        
        detected_objects = []
        for result in results:
            for box in result.boxes:
                class_id = int(box.cls[0])
                class_name = model.names[class_id]
                ru_name = CLASS_NAMES_RU.get(class_name, class_name)
                if ru_name not in detected_objects:
                    detected_objects.append(ru_name)

        if not detected_objects:
            message = "Путь свободен"
        else:
            message = "Впереди: " + ", ".join(detected_objects)

        return JsonResponse({'message': message})


from .services import speech_to_text, analyze_image_local, generate_ai_response_async, text_to_speech_async, read_text_local, detect_objects_local
from .models import VisionUser
import base64
import json
from asgiref.sync import sync_to_async

@method_decorator(csrf_exempt, name='dispatch')
class SmartAnalyzeView(View):
    async def post(self, request, *args, **kwargs):
        # 1. Получаем данные
        image_file = request.FILES.get('image')
        audio_file = request.FILES.get('audio')
        text_input = request.POST.get('text', '')
        user_id = request.POST.get('user_id', 'anonymous')
        mode = request.POST.get('mode', 'chat') # 'chat' or 'navigator'

        # 2. Получаем пользователя
        user_tuple = await sync_to_async(VisionUser.objects.get_or_create)(telegram_id=user_id)
        user = user_tuple[0]

        # 3. Обработка аудио
        if audio_file:
            transcript = await sync_to_async(speech_to_text)(audio_file)
            if transcript:
                text_input = f"{text_input} {transcript}".strip()

        # Если режим навигатора, делаем быстрый детект
        if mode == 'navigator' and image_file:
            image_bytes = image_file.read()
            # Fast YOLO
            objects = await sync_to_async(detect_objects_local)(image_bytes)
            if objects:
                response_text = ", ".join(objects)
            else:
                response_text = "" # Silence if nothing found
            
            # Вернем без сохранения в историю
            return JsonResponse({'message': response_text, 'audio': None})
            # Навигатор обычно озвучивается на клиенте или короткими TTS, 
            # но для скорости вернем текст, фронт может озвучить сам или запросить TTS.
            
        # 4. Обработка Vision (BLIP + OCR)
        visual_description = None
        ocr_text = None
        
        if image_file:
            image_bytes = image_file.read()
            
            # Запускаем BLIP всегда
            visual_description = await sync_to_async(analyze_image_local)(image_bytes)
            
            # Запускаем OCR, если в запросе есть "читай" или "текст" или если BLIP мал
            # Или просто всегда для надежности (чуть медленнее)
            if any(w in text_input.lower() for w in ['читай', 'прочти', 'текст', 'написано', 'цифры']):
                 ocr_text = await sync_to_async(read_text_local)(image_bytes)

            if not text_input:
                text_input = "Что изображено?"

        if not text_input:
             return JsonResponse({'message': 'Не удалось распознать запрос.', 'audio': None})
             
        # Сохраняем запрос пользователя
        await sync_to_async(user.add_message)("user", text_input)

        # 5. LLM
        response_text = await generate_ai_response_async(
            text_input, 
            visual_context=visual_description, 
            user_obj=user,
            ocr_context=ocr_text
        )

        # Сохраняем ответ
        await sync_to_async(user.add_message)("assistant", response_text)

        # 6. TTS
        audio_content = await text_to_speech_async(response_text)
        audio_b64 = None
        if audio_content:
            audio_b64 = base64.b64encode(audio_content).decode('utf-8')

        return JsonResponse({
            'message': response_text,
            'audio': audio_b64,
            'debug_vision': visual_description
        })

def index(request):
    from django.shortcuts import render
    return render(request, 'index.html')

