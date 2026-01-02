from django.db import models

class VisionUser(models.Model):
    telegram_id = models.CharField(max_length=50, unique=True)
    context = models.JSONField(default=list) # История диалога
    facts = models.JSONField(default=dict)   # CAG: Факты о пользователе
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def add_message(self, role, content):
        """Добавить сообщение в историю (храним последние 10)"""
        self.context.append({"role": role, "content": content})
        if len(self.context) > 20: # Храним последние 10 пар
            self.context = self.context[-20:]
        self.save()

    def get_context_text(self):
        """Сформировать текстовое представление истории"""
        return "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.context])

