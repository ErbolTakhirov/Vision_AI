import json
import os
import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class UserMemory:
    """
    Управляет долгосрочным профилем пользователя.
    Хранит данные в JSON файле.
    """
    def __init__(self, filepath: str):
        self.filepath = filepath
        self.profile = self._load_profile()

    def _get_default_profile(self) -> Dict[str, Any]:
        return {
            "name": None,
            "age": None,
            "occupation": None,
            "interests": [],
            "goals": [],
            "preferred_language": "ru",
            "last_interactions": []
        }

    def _load_profile(self) -> Dict[str, Any]:
        if not os.path.exists(self.filepath):
            logger.info("Профиль не найден, создаем новый.")
            return self._get_default_profile()
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Ошибка загрузки профиля: {e}")
            return self._get_default_profile()

    def save_profile(self):
        try:
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(self.profile, f, ensure_ascii=False, indent=2)
            logger.info("Профиль сохранен.")
        except Exception as e:
            logger.error(f"Ошибка сохранения профиля: {e}")

    def update_from_extraction(self, extracted_data: Dict[str, Any]):
        """
        Обновляет профиль на основе данных, извлеченных LLM.
        Пример extracted_data: {"name": "Айбек", "new_interest": "Python"}
        """
        changed = False
        
        if extracted_data.get("name"):
            self.profile["name"] = extracted_data["name"]
            changed = True
            
        if extracted_data.get("occupation"):
            self.profile["occupation"] = extracted_data["occupation"]
            changed = True

        if extracted_data.get("new_interest"):
            interest = extracted_data["new_interest"]
            if interest not in self.profile["interests"]:
                self.profile["interests"].append(interest)
                changed = True

        if changed:
            self.save_profile()

    def get_summary(self) -> str:
        """Возвращает текстовое описание для подстановки в промпт LLM."""
        p = self.profile
        lines = []
        
        name = p.get("name", "Пользователь")
        lines.append(f"Имя пользователя: {name}")
        
        if p.get("occupation"):
            lines.append(f"Деятельность: {p['occupation']}")
            
        if p.get("interests"):
            lines.append(f"Интересы: {', '.join(p['interests'])}")
            
        return "\n".join(lines)
