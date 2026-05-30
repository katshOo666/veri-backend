import base64
import os
import requests
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Настройка CORS, чтобы Wix мог общаться с бэкендом
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Твои данные Sightengine (вшиты намертво для надежности)
SIGHTENGINE_USER = "145435152"
SIGHTENGINE_SECRET = "wa4ykGt9ezK2MUZuTCURcfL2wDjYXpi8"
API_URL = "https://api.sightengine.com/1.0/check.json"

@app.get("/")
def home():
    return {"status": "Live", "mode": "Direct Binary Transfer"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_b64 = body.get("image", "")

        if not image_b64:
            return {"error": True, "message": "Изображение не передано."}

        # Очищаем строку base64 от возможных заголовков браузера
        if "," in image_b64:
            image_b64 = image_b64.split(",")[1]
            
        # Декодируем текстовую строку обратно в байты файла
        img_bytes = base64.b64decode(image_b64)

        # Конфигурация запроса к Sightengine
        params = {
            'models': 'genai', # Модель для распознавания Midjourney, DALL-E (GPT), Nano Banana и др.
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET
        }
        
        # Передаем картинку как файл. Sightengine ТОЧНО её прочитает!
        files = {'media': ('image.jpg', img_bytes, 'image/jpeg')}

        response = requests.post(API_URL, params=params, files=files)
        data = response.json()

        if data.get('status') == 'failure':
            return {"error": True, "message": data.get('error', {}).get('message', 'Ошибка API')}

        # Считываем вероятность генерации ИИ
        ai_prob = data.get('genai', {}).get('prob', 0)

        return {
            "is_ai": ai_prob > 0.5, # Если выше 50% — это ИИ
            "percentage": round(ai_prob * 100, 1),
            "error": False
        }
        
    except Exception as e:
        return {"error": True, "message": "Ошибка обработки на сервере."}
