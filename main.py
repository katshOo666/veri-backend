import os
import re
import requests
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ВСТАВЬ СВОИ ДАННЫЕ СЮДА:
SIGHTENGINE_USER = "145435152"
SIGHTENGINE_SECRET = "wa4ykGt9ezK2MUZuTCURcfL2wDjYXpi8"
API_URL = "https://api.sightengine.com/1.0/check.json"

@app.get("/")
def home():
    return {"status": "Live"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        raw_url = body.get("imageUrl", "")
        
        print(f"Получен URL: {raw_url}")  # Для отладки
        
        if not raw_url:
            return {"error": True, "message": "URL изображения не предоставлен"}
        
        # --- УЛУЧШЕННАЯ ОБРАБОТКА Wix ССЫЛОК ---
        final_url = None
        
        # Случай 1: Обычная ссылка на Wix
        if "wixstatic.com" in raw_url:
            final_url = raw_url
        
        # Случай 2: Специальный формат wix:image
        elif "wix:image" in raw_url:
            # Пробуем разные паттерны
            patterns = [
                r'wix:image://v1/([^/?#]+)',
                r'wix:image://([^/?#]+)',
                r'v1/([a-f0-9]+)',
                r'media/([a-f0-9]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, raw_url)
                if match:
                    img_id = match.group(1)
                    final_url = f"https://static.wixstatic.com/media/{img_id}"
                    break
        
        # Случай 3: Обычный URL
        elif raw_url.startswith("http"):
            final_url = raw_url
        
        # Если не удалось обработать
        if not final_url:
            return {"error": True, "message": f"Не удалось обработать ссылку: {raw_url[:100]}"}
        
        print(f"Обработанный URL: {final_url}")
        
        # --- ПРОВЕРКА ДОСТУПНОСТИ ИЗОБРАЖЕНИЯ ---
        # Проверяем, что изображение вообще доступно
        try:
            test_response = requests.head(final_url, timeout=10)
            if test_response.status_code != 200:
                return {"error": True, "message": f"Изображение не найдено (статус: {test_response.status_code})"}
        except:
            pass
        
        # --- ЗАПРОС К SIGHTENGINE ---
        params = {
            'models': 'genai',  # Модель для обнаружения AI
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET,
            'url': final_url
        }
        
        # Добавляем заголовки для имитации браузера
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(API_URL, params=params, headers=headers, timeout=30)
        data = response.json()
        
        print(f"Ответ Sightengine: {data}")  # Для отладки
        
        # Проверка на ошибки
        if data.get('status') == 'failure':
            error_msg = data.get('error', {}).get('message', 'Неизвестная ошибка')
            return {"error": True, "message": f"Sightengine: {error_msg}"}
        
        # Получаем вероятность AI
        ai_prob = 0
        if 'genai' in data:
            ai_prob = data['genai'].get('prob', 0)
        elif 'type' in data and 'ai' in data['type']:
            # Альтернативный формат ответа
            ai_prob = data['type']['ai']
        
        # Дополнительная проверка: если вероятность очень низкая или высокая
        # Усиливаем контраст для более четкого определения
        if ai_prob > 0.7:
            confidence = "высокая"
        elif ai_prob > 0.5:
            confidence = "средняя"
        elif ai_prob > 0.3:
            confidence = "низкая"
        else:
            confidence = "очень низкая"
        
        # Возвращаем результат
        return {
            "is_ai": ai_prob > 0.5,  # Порог 50%
            "percentage": round(ai_prob * 100, 1),
            "confidence": confidence,
            "raw_score": ai_prob,
            "error": False
        }
        
    except requests.exceptions.Timeout:
        return {"error": True, "message": "Превышено время ожидания. Попробуйте еще раз."}
    except requests.exceptions.RequestException as e:
        return {"error": True, "message": f"Ошибка соединения: {str(e)}"}
    except Exception as e:
        print(f"Общая ошибка: {str(e)}")
        return {"error": True, "message": "Ошибка сервера. Попробуйте еще раз."}

# Дополнительный endpoint для тестирования
@app.post("/test-url")
async def test_url(request: Request):
    """Тестовый endpoint для проверки обработки URL"""
    try:
        body = await request.json()
        raw_url = body.get("imageUrl", "")
        
        # Просто возвращаем информацию о URL
        return {
            "original_url": raw_url,
            "contains_wix": "wix" in raw_url.lower(),
            "contains_static": "wixstatic" in raw_url.lower(),
            "is_wix_format": "wix:image" in raw_url
        }
    except Exception as e:
        return {"error": str(e)}
