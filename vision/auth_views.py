from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, get_user_model
from .serializers import UserRegistrationSerializer, UserLoginSerializer, UserProfileSerializer

User = get_user_model()

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """
    Регистрация нового пользователя
    
    POST /api/auth/register/
    {
        "username": "user123",
        "email": "user@example.com",
        "password": "securepass123",
        "password_confirm": "securepass123",
        "preferred_language": "ru"
    }
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token = Token.objects.get(user=user)
        return Response({
            'token': token.key,
            'user': UserProfileSerializer(user).data,
            'message': 'Registration successful'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """
    Вход пользователя
    
    POST /api/auth/login/
    {
        "username": "user123",
        "password": "securepass123"
    }
    """
    serializer = UserLoginSerializer(data=request.data)
    if serializer.is_valid():
        user = authenticate(
            username=serializer.validated_data['username'],
            password=serializer.validated_data['password']
        )
        if user:
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                'token': token.key,
                'user': UserProfileSerializer(user).data,
                'message': 'Login successful'
            })
        return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Выход пользователя (удаление токена)
    
    POST /api/auth/logout/
    Headers: Authorization: Token <token>
    """
    request.user.auth_token.delete()
    return Response({'message': 'Logout successful'})

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def profile(request):
    """
    Получение/обновление профиля
    
    GET /api/auth/profile/
    Headers: Authorization: Token <token>
    
    PUT /api/auth/profile/
    {
        "preferred_language": "en",
        "voice_speed": 1.2
    }
    """
    if request.method == 'GET':
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_limits(request):
    """
    Проверка лимитов пользователя
    
    GET /api/auth/check-limits/
    """
    user = request.user
    can_request = user.can_make_request()
    
    limits = {'free': 10, 'premium': 999999, 'pro': 999999}
    limit = limits.get(user.subscription_type, 10)
    remaining = max(0, limit - user.daily_requests_count)
    
    return Response({
        'can_make_request': can_request,
        'subscription_type': user.subscription_type,
        'daily_limit': limit,
        'requests_used': user.daily_requests_count,
        'requests_remaining': remaining,
        'total_requests': user.total_requests
    })

@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """
    Авторизация через Google
    
    POST /api/auth/google/
    {
        "access_token": "google_id_token_from_flutter"
    }
    """
    from google.oauth2 import id_token
    from google.auth.transport import requests as google_requests
    import time
    import logging
    
    logger = logging.getLogger(__name__)
    
    token = request.data.get('access_token')
    logger.info(f"🔐 Google Auth Request received. Token present: {bool(token)}")
    
    if not token:
        logger.error("❌ No token provided")
        return Response({'error': 'No token provided'}, status=status.HTTP_400_BAD_REQUEST)
        
    try:
        logger.info("🔍 Verifying Google ID token...")
        # ВНИМАНИЕ: Здесь нужно будет указать ваш CLIENT_ID из Google Cloud Console
        # Для Android приложений CLIENT_ID может проверяться на стороне Google, 
        # но на бэкенде нам главное получить payload.
        # Пока ставим None для audience, но в проде лучше указать список допустимых CLIENT_ID
        
        id_info = id_token.verify_oauth2_token(token, google_requests.Request())
        logger.info(f"✅ Token verified. ID Info: {id_info.get('email')}, {id_info.get('name')}")

        # Если токен протух
        if id_info['exp'] < time.time():
             logger.error("❌ Token expired")
             return Response({'error': 'Token expired'}, status=status.HTTP_400_BAD_REQUEST)

        email = id_info.get('email')
        name = id_info.get('name', '')
        
        if not email:
            logger.error("❌ Email not found in token")
            return Response({'error': 'Email not found in token'}, status=status.HTTP_400_BAD_REQUEST)
            
        logger.info(f"📧 Email from Google: {email}")
        
        # Ищем или создаем пользователя
        user_created = False
        try:
            user = User.objects.get(email=email)
            logger.info(f"👤 Existing user found: {user.username}")
        except User.DoesNotExist:
            logger.info("👤 Creating new user from Google account...")
            # Создаем нового без пароля (так как вход через соцсеть)
            username = email.split('@')[0]
            # Убедимся что username уникален
            base_username = username
            counter = 1
            while User.objects.filter(username=username).exists():
                username = f"{base_username}{counter}"
                counter += 1
                
            user = User.objects.create_user(
                username=username,
                email=email,
            )
            # Устанавливаем unusable password для OAuth пользователей
            user.set_unusable_password()
            user.save()
            user_created = True
            logger.info(f"✅ New user created: {user.username}")
            
        # Генерируем/получаем наш токен
        token_obj, token_created = Token.objects.get_or_create(user=user)
        logger.info(f"🔑 Token {'created' if token_created else 'retrieved'}: {token_obj.key[:10]}...")
        
        response_data = {
            'token': token_obj.key,
            'user': UserProfileSerializer(user).data,
            'message': 'Google login successful'
        }
        logger.info(f"✅ Google auth successful for {email}")
        
        return Response(response_data)
        
    except ValueError as e:
        logger.error(f"❌ Token validation error: {e}")
        return Response({'error': f'Invalid token: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"❌ Unexpected error in Google auth: {e}", exc_info=True)
        return Response({'error': f'Authentication failed: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
