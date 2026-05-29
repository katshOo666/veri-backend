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
    # Получаем ссылку на картинку из запроса Wix
    body = await request.json()
    image_url = body.get("imageUrl")
    
    api_user = os.getenv('API_USER')
    api_secret = os.getenv('API_SECRET')
    
    # Запрос к нейросети Sightengine по ссылке
    params = {
        'url': image_url,
        'models': 'gen-ai,nudity,wad',
        'api_user': api_user,
        'api_secret': api_secret
    }
    
    try:
        response = requests.get('https://api.sightengine.com/1.0/check.json', params=params)
        data = response.json()

        if data.get('status') == 'failure':
            return {"error": True, "message": data['error']['message']}

        ai_score = data.get('type', {}).get('ai_generated', 0) * 100
        
        return {
            "is_ai": ai_score > 50,
            "percentage": round(ai_score, 2),
            "error": False
        }
    except Exception as e:
        return {"error": True, "message": str(e)}
