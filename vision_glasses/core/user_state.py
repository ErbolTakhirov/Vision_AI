class UserState:
    """
    Отслеживает текущее эмоциональное и физическое состояние пользователя.
    """
    def __init__(self):
        self.state = {
            "mood": "neutral",      # neutral, happy, stressed, tired
            "energy": "normal",     # high, normal, low
        }

    def update(self, user_text: str, context: dict):
        """
        Обновляет состояние на основе правил (Rule-based).
        """
        text = user_text.lower()
        
        # Эвристики для усталости
        if any(w in text for w in ["устал", "спать", "нет сил", "тяжело"]):
            self.state["energy"] = "low"
            self.state["mood"] = "tired"
            
        # Эвристики для радости
        elif any(w in text for w in ["классно", "супер", "рад", "отлично"]):
            self.state["mood"] = "happy"
            
        # Эвристики для стресса
        elif any(w in text for w in ["не успеваю", "проблема", "ошибка", "черт"]):
            self.state["mood"] = "stressed"
            
        # Сброс (можно добавить таймер сброса)
        else:
            # Если уже вечер и долго работаем? (Пока оставим простым)
            pass

    def get_state_description(self) -> str:
        mood_ru = {
            "neutral": "спокойное",
            "happy": "радостное",
            "stressed": "напряженное",
            "tired": "уставшее"
        }
        return f"Настроение: {mood_ru.get(self.state['mood'], 'обычное')}, Энергия: {self.state['energy']}"
