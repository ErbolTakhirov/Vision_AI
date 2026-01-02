from django.urls import path
from .views import DetectAPIView, SmartAnalyzeView, index

urlpatterns = [
    path('', index, name='index'),
    path('api/detect/', DetectAPIView.as_view(), name='detect_api'),
    path('api/smart-analyze/', SmartAnalyzeView.as_view(), name='smart_analyze_api'),
]
