import logging

# Заглушка, в реальности тут будет import openai / llama_cpp
def mock_llm_inference(system_prompt, user_prompt):
    """Эмуляция ответа LLM для локального теста без API ключей."""
    user_prompt = user_prompt.lower()
    
    if "как тебя зовут" in user_prompt:
        return "Я A-Vision, твой умный помощник."
    if "устал" in user_prompt:
        return "Отдохни немного. Может, выпьем кофе?"
    if "вижу" in user_prompt:
        return "Я тоже вижу эти объекты. Интересная сцена."
        
    return "Понял тебя. Продолжаем работу."

class DialogManager:
    """
    Управляет диалогом: собирает промпт (CAG) и генерирует ответ.
    """
    def __init__(self, user_memory, user_state):
        self.memory = user_memory
        self.state = user_state
        self.logger = logging.getLogger(__name__)

    def build_system_prompt(self, context_dict: dict) -> str:
        # 1. Данные пользователя
        user_summary = self.memory.get_summary()
        
        # 2. Состояние
        state_desc = self.state.get_state_description()
        
        # 3. Базовая роль
        prompt = (
            f"Ты — умный ассистент в очках дополненной реальности. "
            f"Твоя цель — помогать пользователю кратко и по делу.\n\n"
            f"О ПОЛЬЗОВАТЕЛЕ:\n{user_summary}\n\n"
            f"ТЕКУЩЕЕ СОСТОЯНИЕ:\n{state_desc}\n\n"
            f"КОНТЕКСТ:\n"
            f"Время: {context_dict['time']} ({context_dict['situation']})\n"
            f"Вокруг: {context_dict['visual_scene']}\n"
            f"Видимый текст: {context_dict['visual_text']}\n\n"
            f"Отвечай коротко (1-2 предложения). Будь эмпатичным."
        )
        return prompt

    def generate_response(self, context_dict: dict) -> str:
        user_text = context_dict.get("user_say", "")
        if not user_text:
            return ""

        # 1. Update State before answering
        self.state.update(user_text, context_dict)
        
        # 2. Check for memory updates (Mock extraction)
        # В реальности тут нужен отдельный LLM call или extraction logic
        if "меня зовут" in user_text.lower():
            parts = user_text.split()
            # Очень глупый парсинг для примера
            if len(parts) > 2: 
                self.memory.update_from_extraction({"name": parts[-1]})

        # 3. Build Prompt
        system_prompt = self.build_system_prompt(context_dict)
        
        # 4. LLM Call
        # response = openai.ChatCompletion...
        response = mock_llm_inference(system_prompt, user_text)
        
        return response
