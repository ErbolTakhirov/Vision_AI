from typing import List, Dict, Any
from datetime import datetime

class ContextManager:
    """
    Агрегирует данные с сенсоров (Vision, Audio, Time) в единый контекст.
    """
    def __init__(self):
        self.current_context = {
            "vision_objects": [],
            "vision_text": None,
            "user_last_phrase": None,
            "timestamp": None,
            "situation": "unknown"
        }

    def update_vision(self, objects: List[str], ocr_text: str = None):
        self.current_context["vision_objects"] = objects
        if ocr_text:
            self.current_context["vision_text"] = ocr_text
        self.current_context["timestamp"] = datetime.now()

    def update_speech(self, text: str):
        self.current_context["user_last_phrase"] = text
        self.current_context["timestamp"] = datetime.now()

    def determine_situation(self):
        # Простая эвристика времени суток
        hour = datetime.now().hour
        if 9 <= hour <= 18:
            time_desc = "рабочее время"
        elif 19 <= hour <= 23:
            time_desc = "вечер"
        else:
            time_desc = "ночь"
            
        return time_desc

    def build_context_dict(self) -> Dict[str, Any]:
        """Возвращает чистый словарь для LLM"""
        ctx = self.current_context
        
        vision_desc = "ничего особенного"
        if ctx["vision_objects"]:
            vision_desc = ", ".join(ctx["vision_objects"])
        
        return {
            "time": datetime.now().strftime("%H:%M"),
            "situation": self.determine_situation(),
            "visual_scene": vision_desc,
            "visual_text": ctx["vision_text"] or "нет текста",
            "user_say": ctx["user_last_phrase"]
        }
