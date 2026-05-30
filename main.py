import base64
import os
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

SIGHTENGINE_USER = "145435152"
SIGHTENGINE_SECRET = "wa4ykGt9ezK2MUZuTCURcfL2wDjYXpi8"
API_URL = "https://api.sightengine.com/1.0/check.json"

@app.get("/")
def home():
    return {"status": "Live"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_b64 = body.get("image", "")

        if not image_b64:
            return {"error": True, "message": "Данные картинки не получены сервером"}

        # Раскодируем идеальную Base64 строчку обратно в байты
        img_bytes = base64.b64decode(image_b64)

        params = {
            'models': 'genai',
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET
        }
        
        # Отправляем как полноценный чистый файл
        files = {'media': ('image.jpg', img_bytes, 'image/jpeg')}
        response = requests.post(API_URL, params=params, files=files)
        data = response.json()

        if data.get('status') == 'failure':
            return {"error": True, "message": data.get('error', {}).get('message')}

        ai_prob = data.get('genai', {}).get('prob', 0)
        
        return {
            "is_ai": ai_prob > 0.5,
            "percentage": round(ai_prob * 100, 1),
            "error": False
        }
    except Exception as e:
        return {"error": True, "message": f"Ошибка сервера: {str(e)[:30]}"}
