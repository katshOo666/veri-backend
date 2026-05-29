import os
import re
import time
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Загружаем ключи из переменных окружения (настрой их в Render)
load_dotenv()

app = FastAPI()

# Разрешаем Wix делать запросы к нашему серверу
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Данные Sightengine (обязательно добавь их в Render Settings -> Environment Variables)
SIGHTENGINE_USER = os.getenv("SIGHTENGINE_USER")
SIGHTENGINE_SECRET = os.getenv("SIGHTENGINE_SECRET")
API_URL = "https://api.sightengine.com/1.0/check.json"

@app.get("/")
def home():
    return {"status": "Live", "service": "Sightengine AI Detector"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        raw_url = body.get("imageUrl", "")

        if not raw_url:
            return {"error": True, "message": "Ссылка на картинку пуста"}

        # --- ТРАНСФОРМАЦИЯ ССЫЛКИ WIX ---
        # Wix присылает: wix:image://v1/660415_...jpg/file.jpg#originWidth=...
        # Нам нужно: https://static.wixstatic.com/media/660415_...jpg
        final_url = raw_url
        if "wix:image" in raw_url:
            # Ищем ID файла (обычно это часть между v1/ и следующим /)
            match = re.search(r'v1/([^/]+)', raw_url)
            if match:
                img_id = match.group(1)
                final_url = f"https://static.wixstatic.com/media/{img_id}"

        # --- ЗАПРОС В SIGHTENGINE ---
        params = {
            'models': 'genai',
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET,
            'url': final_url
        }

        response = requests.get(API_URL, params=params)
        data = response.json()

        # Проверка ответа от API
        if data.get('status') == 'failure':
            return {"error": True, "message": data.get('error', {}).get('message', 'Ошибка API')}

        # Получаем вероятность AI (значение от 0 до 1)
        ai_prob = data.get('genai', {}).get('prob', 0)
        
        return {
            "is_ai": ai_prob > 0.5,
            "percentage": round(ai_prob * 100, 1),
            "error": False
        }

    except Exception as e:
        return {"error": True, "message": f"Ошибка сервера: {str(e)[:50]}"}
