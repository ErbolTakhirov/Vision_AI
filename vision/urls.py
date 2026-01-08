from django.urls import path
from .views import DetectAPIView, SmartAnalyzeView, NavigationView, index
from . import auth_views

urlpatterns = [
    path('', index, name='index'),
    
    # Authentication
    path('api/auth/register/', auth_views.register, name='register'),
    path('api/auth/login/', auth_views.login, name='login'),
    path('api/auth/google/', auth_views.google_auth, name='google_auth'),
    path('api/auth/logout/', auth_views.logout, name='logout'),
    path('api/auth/profile/', auth_views.profile, name='profile'),
    path('api/auth/check-limits/', auth_views.check_limits, name='check_limits'),
    
    # Vision AI
    path('api/detect/', DetectAPIView.as_view(), name='detect_api'),
    path('api/smart-analyze/', SmartAnalyzeView.as_view(), name='smart_analyze_api'),
    path('api/navigate/', NavigationView.as_view(), name='navigate_api'),
]
