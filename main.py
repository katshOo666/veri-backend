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

API_URL = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"

@app.get("/")
def home():
    return {"status": "Work"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_url = body.get("imageUrl")
        
        # Улучшенная магия для Wix-ссылок
        if "wix:image" in image_url:
            # Извлекаем ID картинки точнее
            parts = image_url.split('/')
            img_id = [p for p in parts if '.' in p or '_' in p][0]
            if '#' in img_id: img_id = img_id.split('#')[0]
            image_url = f"https://static.wixstatic.com/media/{img_id}"
        
        # Качаем картинку
        img_resp = requests.get(image_url, timeout=10)
        if img_resp.status_code != 200:
            return {"error": True, "message": "Не удалось загрузить фото из Wix"}

        # Пробуем нейросеть
        for i in range(5):
            response = requests.post(API_URL, data=img_resp.content, timeout=15)
            data = response.json()
            
            if isinstance(data, dict) and "estimated_time" in data:
                time.sleep(4)
                continue
            
            if isinstance(data, list):
                # Ищем вероятность ИИ (label_1 или artificial/ai)
                ai_score = 0
                for item in data:
                    label = item.get('label', '').lower()
                    if label in ['artificial', 'ai', 'fake', 'label_1']:
                        ai_score = item.get('score', 0)
                
                return {
                    "is_ai": ai_score > 0.5,
                    "percentage": round(ai_score * 100, 1),
                    "error": False
                }
        
        return {"error": True, "message": "Нейросеть спит. Нажми еще раз!"}

    except Exception as e:
        return {"error": True, "message": f"Ошибка: {str(e)[:20]}..."}
