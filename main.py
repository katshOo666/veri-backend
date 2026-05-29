from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

# Разрешаем Wix обращаться к серверу
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Veri is Live and Ready"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        # Получаем данные от Wix
        body = await request.json()
        image_url = body.get("imageUrl")
        
        if not image_url:
            return {"error": True, "message": "No image URL provided"}

        # Ключи из настроек Render (Environment)
        api_user = os.getenv('API_USER')
        api_secret = os.getenv('API_SECRET')
        
        # Запрос к Sightengine с правильной моделью
        # Мы используем 'gen-ai', так как она самая точная сейчас
        params = {
            'url': image_url,
            'models': 'gen-ai', 
            'api_user': api_user,
            'api_secret': api_secret
        }
        
        response = requests.get('https://api.sightengine.com/1.0/check.json', params=params)
        data = response.json()

        # Если Sightengine вернул ошибку
        if data.get('status') == 'failure':
            return {"error": True, "message": data['error']['message']}

        # Достаем вероятность того, что это ИИ
        # В модели gen-ai структура ответа именно такая:
        ai_score = data.get('type', {}).get('ai_generated', 0)
        
        # Переводим в проценты (от 0 до 100)
        percentage = round(ai_score * 100, 2)
        
        return {
            "is_ai": percentage > 50, # Если больше 50%, считаем что это ИИ
            "percentage": percentage,
            "error": False
        }
        
    except Exception as e:
        return {"error": True, "message": f"Python Error: {str(e)}"}
