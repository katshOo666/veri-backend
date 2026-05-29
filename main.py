import os
import re
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

# ВСТАВЬ СВОИ ДАННЫЕ СЮДА:
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
        raw_url = body.get("imageUrl", "")

        # Превращаем ссылку Wix в нормальную
        final_url = raw_url
        if "wix:image" in raw_url:
            match = re.search(r'v1/([^/]+)', raw_url)
            if match:
                img_id = match.group(1)
                final_url = f"https://static.wixstatic.com/media/{img_id}"

        # Запрос к Sightengine
        params = {
            'models': 'genai',
            'api_user': SIGHTENGINE_USER,
            'api_secret': SIGHTENGINE_SECRET,
            'url': final_url
        }

        response = requests.get(API_URL, params=params)
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
        return {"error": True, "message": "Ошибка сервера. Попробуй еще раз."}
