import os
import re
import base64
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

app = FastAPI()

# Максимально широкие CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SIGHTENGINE_USER = "145435152"
SIGHTENGINE_SECRET = "wa4ykGt9ezK2MUZuTCURcfL2wDjYXpi8"
API_URL = "https://api.sightengine.com/1.0/check.json"

@app.get("/")
def home():
    return {"status": "Live", "message": "AI Detector работает"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_base64 = body.get("imageBase64", "")
        image_url = body.get("imageUrl", "")

        img_data = None

        # Приоритет: base64 (самый надёжный)
        if image_base64:
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]
            img_data = base64.b64decode(image_base64)
        elif image_url:
            # Обработка Wix URL
            final_url = image_url
            if "wix:image" in image_url:
                parts = image_url.split('/')
                if len(parts) > 3:
                    final_url = f"https://static.wixstatic.com/media/{parts[3]}"
            # Скачиваем картинку
            resp = requests.get(final_url, timeout=15)
            resp.raise_for_status()
            img_data = resp.content

        if not img_data:
            return JSONResponse(content={"error": True, "message": "Не удалось получить изображение"}, status_code=400)

        # Отправляем в Sightengine файлом
        params = {
            'models': 'genai',
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET,
        }
        files = {'media': ('image.jpg', img_data, 'image/jpeg')}
        response = requests.post(API_URL, params=params, files=files, timeout=30)
        data = response.json()

        if data.get('status') == 'failure':
            return JSONResponse(content={"error": True, "message": data.get('error', {}).get('message')}, status_code=400)

        ai_prob = data.get('genai', {}).get('prob', 0)
        return {
            "is_ai": ai_prob > 0.5,
            "percentage": round(ai_prob * 100, 1),
            "error": False
        }

    except Exception as e:
        return JSONResponse(content={"error": True, "message": str(e)}, status_code=500)
