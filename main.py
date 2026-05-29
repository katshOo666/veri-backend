import os
import base64
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Берем ключи из переменных Render
SIGHTENGINE_USER = os.getenv("145435152")
SIGHTENGINE_SECRET = os.getenv("wa4ykGt9ezK2MUZuTCURcfL2wDjYXpi8")

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_b64 = body.get("image") # Получаем картинку как текст

        if not image_b64:
            return {"error": True, "message": "Данные изображения не получены"}

        # Декодируем Base64 в байты
        if "," in image_b64:
            image_b64 = image_b64.split(",")[1]
        img_bytes = base64.b64decode(image_b64)

        # Отправляем в Sightengine как файл (Multipart)
        params = {
            'models': 'genai',
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET,
        }
        files = {'media': ('image.jpg', img_bytes, 'image/jpeg')}
        
        response = requests.post('https://api.sightengine.com/1.0/check.json', params=params, files=files)
        data = response.json()

        if data.get('status') == 'failure':
            return {"error": True, "message": data.get('error', {}).get('message')}

        ai_score = data.get('genai', {}).get('prob', 0)
        
        return {
            "is_ai": ai_score > 0.5,
            "percentage": round(ai_score * 100, 1),
            "error": False
        }
    except Exception as e:
        return {"error": True, "message": f"Ошибка сервера: {str(e)[:40]}"}
