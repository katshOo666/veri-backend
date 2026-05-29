from fastapi import FastAPI, UploadFile, File
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
    return {"status": "Veri Backend is running"}

@app.post("/analyze")
async def analyze(image: UploadFile = File(...)):
    # Получаем ключи из настроек Render (Environment Variables)
    # Если ты их еще не вставила в Render, можно временно вписать их вместо os.getenv
    api_user = os.getenv('API_USER')
    api_secret = os.getenv('API_SECRET')
    
    file_bytes = await image.read()
    
    # Запрос к нейросети Sightengine
    params = {
        'models': 'gen-ai,nudity,wad',
        'api_user': api_user,
        'api_secret': api_secret
    }
    
    files = {'media': file_bytes}
    
    try:
        response = requests.post('https://api.sightengine.com/1.0/check.json', files=files, data=params)
        data = response.json()

        if data.get('status') == 'failure':
            return {"error": True, "message": data['error']['message']}

        # Анализ на ИИ
        ai_score = data.get('type', {}).get('ai_generated', 0) * 100
        
        # Анализ на запрещенку (нагота или оружие)
        is_nude = data.get('nudity', {}).get('raw', 0) > 0.5
        has_weapon = data.get('weapon', 0) > 0.5

        if is_nude or has_weapon:
            return {
                "error": True, 
                "message": "Контент заблокирован: обнаружен непристойный материал или насилие."
            }
        
        return {
            "is_ai": ai_score > 50,
            "percentage": round(ai_score, 2),
            "message": "Это ИИ-генерация" if ai_score > 50 else "Это реальное фото",
            "error": False
        }
        
    except Exception as e:
        return {"error": True, "message": str(e)}
