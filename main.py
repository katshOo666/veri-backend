import os
import base64
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Настройка CORS для связи с Wix
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ключи Sightengine (обязательно добавьте их в Environment Variables на Render)
SIGHTENGINE_USER = os.getenv("SIGHTENGINE_USER")
SIGHTENGINE_SECRET = os.getenv("SIGHTENGINE_SECRET")
SIGHTENGINE_API_URL = "https://api.sightengine.com/1.0/check.json"

@app.get("/")
def home():
    return {"status": "online", "model": "genai_detector"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        
        # Обработка входящих данных (поддержка URL и Base64 для надежности)
        image_url = body.get("imageUrl", "")
        image_b64 = body.get("image", "")

        params = {
            'models': 'genai', # Модель для Midjourney, DALL-E, Nano Banana и др.
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET,
        }

        # МЕТОД 1: Если Wix прислал саму картинку (Base64) - самый надежный способ
        if image_b64:
            if "," in image_b64:
                image_b64 = image_b64.split(",")[1]
            img_bytes = base64.b64decode(image_b64)
            files = {'media': ('image.jpg', img_bytes, 'image/jpeg')}
            response = requests.post(SIGHTENGINE_API_URL, params=params, files=files)
        
        # МЕТОД 2: Если пришла ссылка (используется как запасной вариант)
        elif image_url:
            # Очистка ссылки Wix
            final_url = image_url.split('#')[0].replace('wix:image://v1/', 'https://static.wixstatic.com/media/')
            params['url'] = final_url
            response = requests.get(SIGHTENGINE_API_URL, params=params)
        
        else:
            return {"error": True, "message": "Данные изображения не получены"}

        result = response.json()

        # Проверка ответа от Sightengine
        if result.get('status') != 'success':
            return {"error": True, "message": result.get('error', {}).get('message', 'API Error')}

        # Получаем вероятность ИИ (от 0 до 1)
        ai_prob = result.get('genai', {}).get('prob', 0)
        
        return {
            "is_ai": ai_prob > 0.5, # Порог срабатывания
            "percentage": round(ai_prob * 100, 1),
            "error": False,
            "source": "sightengine_genai"
        }

    except Exception as e:
        return {"error": True, "message": f"Server Error: {str(e)[:50]}"}
