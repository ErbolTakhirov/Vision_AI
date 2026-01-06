from datetime import datetime

class Brain:
    def process(self, text):
        """
        Processing logic. Replace this with LLM call.
        """
        text = text.lower()
        
        if "время" in text or "который час" in text:
            now = datetime.now().strftime("%H:%M")
            return f"Сейчас {now}"
            
        if "планет" in text:
            return "В Солнечной системе восемь планет."
            
        if "кто ты" in text:
            return "Я голосовой ассистент A-Vision."
            
        return "Я услышал: " + text + ", но пока не знаю что ответить."
