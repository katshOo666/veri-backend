import base64
import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Разрешаем Wix подключаться к серверу
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Твои данные Sightengine (вшиты для надежности)
SIGHTENGINE_USER = "145435152"
SIGHTENGINE_SECRET = "wa4ykGt9ezK2MUZuTCURcfL2wDjYXpi8"
API_URL = "https://api.sightengine.com/1.0/check.json"

@app.get("/")
def home():
    return {"status": "Live", "info": "Veri AI Detector"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_b64 = body.get("image", "")
        image_url = body.get("imageUrl", "")

        params = {
            'models': 'genai', # Модель распознавания Nano Banana, Midjourney, DALL-E и др.
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET
        }

        # Способ 1: Если Wix прислал саму картинку кодом (Самый точный и надежный)
        if image_b64:
            if "," in image_b64:
                image_b64 = image_b64.split(",")[1]
            img_bytes = base64.b64decode(image_b64)
            files = {'media': ('image.jpg', img_bytes, 'image/jpeg')}
            response = requests.post(API_URL, params=params, files=files)
            
        # Способ 2: Резервный (если пришла ссылка)
        elif image_url:
            final_url = image_url.split('#')[0].replace('wix:image://v1/', 'https://static.wixstatic.com/media/')
            params['url'] = final_url
            response = requests.get(API_URL, params=params)
            
        else:
            return {"error": True, "message": "Файл изображения не найден в запросе"}

        data = response.json()

        if data.get('status') == 'failure':
            return {"error": True, "message": data.get('error', {}).get('message')}

        # Извлекаем точный процент ИИ
        ai_prob = data.get('genai', {}).get('prob', 0)
        
        return {
            "is_ai": ai_prob > 0.5, # Порог 50%
            "percentage": round(ai_prob * 100, 1),
            "error": False
        }
    except Exception as e:
        return {"error": True, "message": "Внутренняя ошибка бэкенда"}
