import logging
from datetime import datetime
from .models import VisionUser

logger = logging.getLogger(__name__)

class CAGSystem:
    """
    Context-Affect-Guidance Orchestrator
    """
    def __init__(self, user: VisionUser):
        self.user = user
        # Инициализация фактов, если пусто
        if not self.user.facts:
            self.user.facts = {
                "name": None,
                "interests": [],
                "mood": "neutral",
                "energy": "normal"
            }

    def update_state(self, user_text: str):
        """Обновляет аффективное состояние (настроение)"""
        text = user_text.lower()
        facts = self.user.facts
        
        # Простейшая эвристика (можно заменить на классификатор)
        if any(w in text for w in ["устал", "спать", "нет сил"]):
            facts["mood"] = "tired"
            facts["energy"] = "low"
        elif any(w in text for w in ["круто", "спасибо", "рад"]):
            facts["mood"] = "happy"
            facts["energy"] = "high"
        elif any(w in text for w in ["привет", "старт"]):
            facts["mood"] = "neutral"
            
        # Обновляем память
        if "меня зовут" in text:
            parts = text.split(" зовут ")
            if len(parts) > 1:
                name = parts[1].split()[0].capitalize()
                facts["name"] = name

        self.user.facts = facts
        self.user.save()

    def build_system_prompt(self, visual_context=None) -> str:
        """Собирает системный промпт для LLM"""
        f = self.user.facts
        
        # 1. Личность
        prompt = (
            "Ты — A-Vision, умный помощник в очках. Твоя цель — помогать пользователю ориентироваться и решать задачи.\n"
            "Отвечай кратко (1-3 предложения), живо и по-человечески.\n\n"
        )
        
        # 2. Профиль пользователя
        if f.get("name"):
            prompt += f"Пользователя зовут {f['name']}. Обращайся по имени иногда.\n"
        
        if f.get("interests"):
            prompt += f"Интересы пользователя: {', '.join(f['interests'])}.\n"
            
        # 3. Состояние (Affect)
        mood_map = {"tired": "У пользователя мало сил, отвечай мягко и поддерживающе.", 
                   "happy": "Пользователь рад, поддерживай позитив!",
                   "neutral": ""}
        prompt += f"{mood_map.get(f.get('mood'), '')}\n\n"
        
        # 4. Контекст времени
        hour = datetime.now().hour
        time_desc = "День" if 9 <= hour < 18 else "Вечер/Ночь"
        prompt += f"Сейчас {time_desc} ({hour}:00).\n"
        
        if visual_context:
            prompt += f"\nТы видишь: {visual_context}\n"
            
        prompt += "\nИнструкция: Если пользователь спрашивает 'что ты видишь', опиши сцену. Если просит помощи, помоги."
        
        return prompt
