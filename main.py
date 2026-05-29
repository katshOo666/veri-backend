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
        
        api_user = os.getenv('API_USER')
        api_secret = os.getenv('API_SECRET')

        # Список возможных названий моделей (от новых к старым)
        models_to_try = ['gen-ai', 'ai-generated', 'artificial']
        
        data = {}
        last_error = ""

        # Пробуем каждую модель, пока не получим ответ
        for model in models_to_try:
            params = {
                'url': image_url,
                'models': model,
                'api_user': api_user,
                'api_secret': api_secret
            }
            response = requests.get('https://api.sightengine.com/1.0/check.json', params=params)
            data = response.json()
            
            # Если модель подошла и ошибки нет — выходим из цикла
            if data.get('status') == 'success':
                break
            else:
                last_error = data.get('error', {}).get('message', 'Unknown error')

        if data.get('status') == 'failure':
            return {"error": True, "message": f"Sightengine error: {last_error}"}

        # Вытаскиваем результат (логика для разных моделей может чуть отличаться)
        # Проверяем все возможные места, где может лежать процент ИИ
        type_data = data.get('type', {})
        ai_score = type_data.get('ai_generated') or data.get('ai_generated') or 0
        
        percentage = round(ai_score * 100, 2)
        
        return {
            "is_ai": percentage > 50,
            "percentage": percentage,
            "error": False
        }
        
    except Exception as e:
        return {"error": True, "message": f"Server error: {str(e)}"}
