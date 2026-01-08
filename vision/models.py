from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    """Расширенная модель пользователя для WayFinder"""
    
    # Профиль
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    
    # Подписка
    subscription_type = models.CharField(
        max_length=20,
        choices=[
            ('free', 'Free'),
            ('premium', 'Premium'),
            ('pro', 'Pro'),
        ],
        default='free'
    )
    subscription_expires = models.DateTimeField(blank=True, null=True)
    
    # Лимиты
    daily_requests_count = models.IntegerField(default=0)
    last_request_date = models.DateField(auto_now=True)
    
    # Настройки
    preferred_language = models.CharField(max_length=5, default='ru')
    voice_speed = models.FloatField(default=1.0)  # Скорость TTS
    
    # Метрики
    total_requests = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'users'
    
    def __str__(self):
        return self.username
    
    def can_make_request(self):
        """Проверка лимитов запросов"""
        from datetime import date
        
        # Сброс счетчика если новый день
        if self.last_request_date != date.today():
            self.daily_requests_count = 0
            self.save()
        
        # Лимиты по типу подписки
        limits = {
            'free': 10,
            'premium': 999999,  # Безлимит
            'pro': 999999,
        }
        
        return self.daily_requests_count < limits.get(self.subscription_type, 10)
    
    def increment_request_count(self):
        """Увеличить счетчик запросов"""
        self.daily_requests_count += 1
        self.total_requests += 1
        self.save()

class VisionUser(models.Model):
    """
    Модель для хранения истории чата (Legacy/Telegram compatibility)
    """
    telegram_id = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    context = models.TextField(blank=True, null=True) # Хранение истории переписки (JSON или текст)
    
    # CAG System: Персональные факты и состояние пользователя
    facts = models.JSONField(default=dict, blank=True, null=True)
    
    # Связь с новой системой пользователей (опционально)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"VisionUser {self.telegram_id}"

    def add_message(self, role, content):
        """Добавить сообщение в контекст"""
        import json
        try:
            history = json.loads(self.context) if self.context else []
        except:
            history = []
        
        # Ограничиваем историю
        if len(history) > 20: 
            history = history[-20:]
            
        history.append({"role": role, "content": content})
        self.context = json.dumps(history, ensure_ascii=False)
        self.save()
        
    def get_context(self):
        """Получить историю как список словарей"""
        import json
        try:
            return json.loads(self.context) if self.context else []
        except:
            return []
