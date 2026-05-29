import os
import base64
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Ключи берем из переменных окружения Render
SIGHTENGINE_USER = os.getenv("145435152")
SIGHTENGINE_SECRET = os.getenv("wa4ykGt9ezK2MUZuTCURcfL2wDjYXpi8")

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_data = body.get("image")

        if not image_data:
            return {"error": True, "message": "Данные изображения отсутствуют"}

        # Очистка и декодирование Base64
        if "," in image_data:
            image_data = image_data.split(",")[1]
        img_bytes = base64.b64decode(image_data)

        # Отправка файла напрямую в API
        params = {
            'models': 'genai',
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET,
        }
        files = {'media': ('image.jpg', img_bytes, 'image/jpeg')}
        
        response = requests.post('https://api.sightengine.com/1.0/check.json', params=params, files=files)
        result = response.json()

        if result.get('status') == 'failure':
            return {"error": True, "message": result.get('error', {}).get('message')}

        ai_prob = result.get('genai', {}).get('prob', 0)
        
        return {
            "is_ai": ai_prob > 0.5,
            "percentage": round(ai_prob * 100, 1),
            "error": False
        }
    except Exception as e:
        return {"error": True, "message": f"Ошибка сервера: {str(e)[:50]}"}
