import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import base64
import re
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- КОНФИГУРАЦИЯ SIGHTENGINE ----
# Замени 'ВАШ_USER' и 'ВАШ_SECRET' на данные из панели Sightengine, 
# если не используешь переменные окружения в Render
SIGHTENGINE_USER = os.getenv("SIGHTENGINE_USER", "ВАШ_USER")
SIGHTENGINE_SECRET = os.getenv("SIGHTENGINE_SECRET", "ВАШ_SECRET")
SIGHTENGINE_API_URL = "https://api.sightengine.com/1.0/check.json"

@app.get("/")
def home():
    return {"status": "OK", "message": "Sightengine Detector is Live"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_url = body.get("imageUrl", "")
        image_base64 = body.get("imageBase64", "")

        params = {
            'models': 'genai',
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET,
        }

        # СЛУЧАЙ 1: Отправка через Base64 (если Wix передает строку)
        if image_base64:
            if "," in image_base64:
                image_base64 = image_base64.split(",")[1]
            img_bytes = base64.b64decode(image_base64)
            
            # ИСПРАВЛЕНО: Правильный формат отправки файлов в requests
            files = {'media': ('image.jpg', img_bytes, 'image/jpeg')}
            response = requests.post(SIGHTENGINE_API_URL, params=params, files=files)

        # СЛУЧАЙ 2: Отправка через URL (включая ссылки Wix)
        elif image_url:
            final_url = image_url
            if "wix:image" in image_url:
                # Улучшенная регулярка для извлечения ID медиа из Wix
                match = re.search(r'v1/(.*?)/', image_url)
                if not match: match = re.search(r'wix:image://v1/(.*?)#', image_url)
                
                if match:
                    img_id = match.group(1)
                    final_url = f"https://static.wixstatic.com/media/{img_id}"
            
            params['url'] = final_url
            response = requests.get(SIGHTENGINE_API_URL, params=params)
        
        else:
            return {"error": True, "message": "Нет данных изображения"}

        # Обработка ответа
        result = response.json()
        
        if result.get('status') == 'failure':
            return {"error": True, "message": result.get('error', {}).get('message')}

        # Получаем вероятность AI
        ai_prob = result.get('genai', {}).get('prob', 0)
        
        return {
            "is_ai": ai_prob > 0.5,
            "percentage": round(ai_prob * 100, 1),
            "error": False,
            "confidence": ai_prob
        }

    except Exception as e:
        return {"error": True, "message": f"Ошибка сервера: {str(e)[:50]}"}
