from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"status": "Veri is Live"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_url = body.get("imageUrl")
        
        # Берем ключи
        api_user = os.getenv('API_USER')
        api_secret = os.getenv('API_SECRET')

        # Запрашиваем сразу все модели, которые отвечают за ИИ
        # Одна из них ТОЧНО должна сработать
        params = {
            'url': image_url,
            'models': 'gen-ai,ai-generated', 
            'api_user': api_user,
            'api_secret': api_secret
        }
        
        response = requests.get('https://api.sightengine.com/1.0/check.json', params=params)
        data = response.json()

        # Если Sightengine ругается на ключи или доступ
        if data.get('status') == 'failure':
            return {"error": True, "message": f"Ошибка Sightengine: {data.get('error', {}).get('message')}"}

        # Вытаскиваем любой намек на ИИ из ответа
        ai_score = 0
        
        # Проверяем структуру gen-ai
        if 'type' in data and 'ai_generated' in data['type']:
            ai_score = data['type']['ai_generated']
        # Проверяем структуру ai-generated
        elif 'ai_generated' in data:
            ai_score = data['ai_generated']
            
        percentage = round(ai_score * 100, 2)
        
        return {
            "is_ai": percentage > 50,
            "percentage": percentage,
            "error": False
        }
        
    except Exception as e:
        return {"error": True, "message": f"Ошибка сервера: {str(e)}"}
