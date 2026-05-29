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

        # Используем стандартную модель модерации, которая часто включает ИИ-детекцию
        params = {
            'url': image_url,
            'models': 'gen-ai', 
            'api_user': api_user,
            'api_secret': api_secret
        }
        
        response = requests.get('https://api.sightengine.com/1.0/check.json', params=params)
        data = response.json()

        # Если Sightengine говорит, что модель неизвестна, попробуем общую модель
        if data.get('status') == 'failure' and 'Unknown model' in data.get('error', {}).get('message', ''):
            params['models'] = 'general'
            response = requests.get('https://api.sightengine.com/1.0/check.json', params=params)
            data = response.json()

        if data.get('status') == 'failure':
            return {"error": True, "message": f"Sightengine: {data['error']['message']}"}

        # Ищем процент ИИ
        ai_score = 0
        if 'type' in data:
            ai_score = data['type'].get('ai_generated', 0)
        elif 'ai_generated' in data:
            ai_score = data.get('ai_generated', 0)
            
        percentage = round(ai_score * 100, 2)
        
        return {
            "is_ai": percentage > 50,
            "percentage": percentage,
            "error": False
        }
        
    except Exception as e:
        return {"error": True, "message": f"Ошибка: {str(e)}"}
