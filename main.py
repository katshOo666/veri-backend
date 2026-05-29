from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import requests
import time

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Самая надежная модель, которая не требует авторизации
API_URL = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_url = body.get("imageUrl")
        img_data = requests.get(image_url).content
        
        # Пытаемся получить ответ 5 раз, если нейросеть грузится
        for i in range(5):
            response = requests.post(API_URL, data=img_data)
            result = response.json()
            
            if isinstance(result, dict) and "estimated_time" in result:
                time.sleep(5)
                continue
            
            if isinstance(result, list):
                ai_score = next((item['score'] for item in result if item['label'].lower() in ['artificial', 'ai', 'fake']), 0)
                return {"is_ai": ai_score > 0.5, "percentage": round(ai_score * 100, 2), "error": False}
        
        return {"error": True, "message": "Почти готово! Нажми еще раз через 5 секунд."}
    except:
        return {"error": True, "message": "Нажми кнопку еще раз."}
