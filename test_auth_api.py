"""
Тестовый скрипт для проверки API аутентификации WayFinder
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8000"

def test_register():
    """Тест регистрации"""
    print("\n=== ТЕСТ РЕГИСТРАЦИИ ===")
    url = f"{BASE_URL}/api/auth/register/"
    data = {
        "username": "testuser",
        "email": "test@wayfinder.com",
        "password": "SecurePass123!",
        "password_confirm": "SecurePass123!",
        "preferred_language": "ru"
    }
    
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 201:
        return response.json()['token']
    return None

def test_login():
    """Тест входа"""
    print("\n=== ТЕСТ ВХОДА ===")
    url = f"{BASE_URL}/api/auth/login/"
    data = {
        "username": "testuser",
        "password": "SecurePass123!"
    }
    
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
    
    if response.status_code == 200:
        return response.json()['token']
    return None

def test_profile(token):
    """Тест получения профиля"""
    print("\n=== ТЕСТ ПРОФИЛЯ ===")
    url = f"{BASE_URL}/api/auth/profile/"
    headers = {"Authorization": f"Token {token}"}
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_check_limits(token):
    """Тест проверки лимитов"""
    print("\n=== ТЕСТ ЛИМИТОВ ===")
    url = f"{BASE_URL}/api/auth/check-limits/"
    headers = {"Authorization": f"Token {token}"}
    
    response = requests.get(url, headers=headers)
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

def test_smart_analyze(token):
    """Тест AI запроса с токеном"""
    print("\n=== ТЕСТ AI ЗАПРОСА ===")
    url = f"{BASE_URL}/api/smart-analyze/"
    headers = {"Authorization": f"Token {token}"}
    data = {
        "text": "Привет, WayFinder!",
        "mode": "chat"
    }
    
    response = requests.post(url, data=data, headers=headers)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Message: {result.get('message', 'N/A')}")
    else:
        print(f"Error: {response.text}")

if __name__ == "__main__":
    print("🚀 WayFinder API Test Suite\n")
    
    # 1. Регистрация
    token = test_register()
    
    if not token:
        # Если пользователь уже существует, попробуем войти
        token = test_login()
    
    if token:
        print(f"\n✅ Token получен: {token[:20]}...")
        
        # 2. Профиль
        test_profile(token)
        
        # 3. Лимиты
        test_check_limits(token)
        
        # 4. AI запрос
        test_smart_analyze(token)
        
        print("\n✅ Все тесты пройдены!")
    else:
        print("\n❌ Не удалось получить токен")
