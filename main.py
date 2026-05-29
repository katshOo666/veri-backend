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

# Используем очень быструю и стабильную модель
API_URL = "https://api-inference.huggingface.co/models/umm-maybe/AI-image-detector"

@app.get("/")
def home():
    return {"status": "Ready to work!"}

@app.post("/analyze")
async def analyze(request: Request):
    try:
        body = await request.json()
        image_url = body.get("imageUrl")
        image_data = requests.get(image_url).content
        
        # Пытаемся спросить нейросеть до 3 раз, если она спит
        for i in range(3):
            response = requests.post(API_URL, data=image_data)
            result = response.json()
            
            # Если нейросеть загружается, ждем 5 секунд и пробуем снова
            if isinstance(result, dict) and "estimated_time" in result:
                time.sleep(5)
                continue
            
            # Если получили результат
            if isinstance(result, list):
                ai_score = 0
                for item in result:
                    if item['label'].lower() in ['artificial', 'ai', 'fake']:
                        ai_score = item['score']
                
                percentage = round(ai_score * 100, 2)
                return {
                    "is_ai": percentage > 50,
                    "percentage": percentage,
                    "error": False
                }
        
        return {"error": True, "message": "Нейросеть просыпается, нажмите кнопку еще раз через 5 секунд"}
        
    except Exception as e:
        return {"error": True, "message": "Сервер перегружен, попробуйте снова"}
